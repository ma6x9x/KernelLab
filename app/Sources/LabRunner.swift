import Darwin
import Foundation

/// Starts `/var/jb/usr/bin/kernellab` with a fixed argv. There is no shell.
enum LabRunner {
    static let candidates = [
        "/var/jb/usr/bin/kernellab",
        "/usr/bin/kernellab",
    ]

    static func run(_ arguments: [String]) -> LabRunResult {
        guard let executable = resolve() else {
            return LabRunResult(
                status: 127,
                output: "kernellab CLI not found. Expected /var/jb/usr/bin/kernellab. Install the kernellab package. This app does not reimplement the harness.",
                executable: ""
            )
        }
        return spawn(executable, arguments)
    }

    private static func resolve() -> String? {
        for path in candidates where FileManager.default.isExecutableFile(atPath: path) {
            return path
        }
        for path in candidates where FileManager.default.fileExists(atPath: path) {
            return path
        }
        return nil
    }

    private static func spawn(_ executable: String, _ arguments: [String]) -> LabRunResult {
        var outPipe: [Int32] = [-1, -1]
        var errPipe: [Int32] = [-1, -1]
        if pipe(&outPipe) != 0 {
            return LabRunResult(status: 1, output: "Could not create pipes for kernellab.", executable: executable)
        }
        if pipe(&errPipe) != 0 {
            close(outPipe[0])
            close(outPipe[1])
            return LabRunResult(status: 1, output: "Could not create pipes for kernellab.", executable: executable)
        }
        defer {
            for fd in outPipe + errPipe where fd >= 0 {
                close(fd)
            }
        }

        var actions: posix_spawn_file_actions_t?
        posix_spawn_file_actions_init(&actions)
        defer { posix_spawn_file_actions_destroy(&actions) }
        posix_spawn_file_actions_adddup2(&actions, outPipe[1], STDOUT_FILENO)
        posix_spawn_file_actions_adddup2(&actions, errPipe[1], STDERR_FILENO)
        posix_spawn_file_actions_addclose(&actions, outPipe[0])
        posix_spawn_file_actions_addclose(&actions, errPipe[0])
        posix_spawn_file_actions_addclose(&actions, outPipe[1])
        posix_spawn_file_actions_addclose(&actions, errPipe[1])

        let argvStrings = [executable] + arguments
        let argvPtrs: [UnsafeMutablePointer<CChar>?] = argvStrings.map { strdup($0) } + [nil]
        let envPtrs: [UnsafeMutablePointer<CChar>?] = environment().map { strdup($0) } + [nil]
        defer {
            for pointer in argvPtrs { free(pointer) }
            for pointer in envPtrs { free(pointer) }
        }

        var pid: pid_t = 0
        let spawned = posix_spawn(&pid, executable, &actions, nil, argvPtrs, envPtrs)
        close(outPipe[1])
        outPipe[1] = -1
        close(errPipe[1])
        errPipe[1] = -1
        if spawned != 0 {
            let message = String(cString: strerror(spawned))
            return LabRunResult(
                status: spawned,
                output: "Could not start kernellab (\(message)).",
                executable: executable
            )
        }

        let collected = collect(pid: pid, outFD: outPipe[0], errFD: errPipe[0])
        close(outPipe[0])
        outPipe[0] = -1
        close(errPipe[0])
        errPipe[0] = -1
        return LabRunResult(status: collected.status, output: collected.text, executable: executable)
    }

    private static func environment() -> [String] {
        let process = ProcessInfo.processInfo.environment
        var path = "/var/jb/usr/bin:/var/jb/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        if let current = process["PATH"], !current.isEmpty {
            path = "/var/jb/usr/bin:/var/jb/bin:" + current
        }
        var values = ["PATH=" + path]
        let keys = [
            "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL",
            "KERNELLAB_CACHES", "KERNELLAB_STATE", "XDG_DATA_HOME",
        ]
        for key in keys {
            guard let value = process[key], !value.isEmpty, !value.contains("\0") else { continue }
            values.append(key + "=" + value)
        }
        if values.contains(where: { $0.hasPrefix("HOME=") }) == false {
            values.append("HOME=" + NSHomeDirectory())
        }
        return values
    }

    private static func collect(pid: pid_t, outFD: Int32, errFD: Int32) -> (status: Int32, text: String) {
        let outFlags = fcntl(outFD, F_GETFL)
        let errFlags = fcntl(errFD, F_GETFL)
        if outFlags >= 0 { _ = fcntl(outFD, F_SETFL, outFlags | O_NONBLOCK) }
        if errFlags >= 0 { _ = fcntl(errFD, F_SETFL, errFlags | O_NONBLOCK) }

        var out = Data()
        var err = Data()
        var outOpen = true
        var errOpen = true
        var status: Int32 = 0
        var reaped = false
        var timedOut = false
        var truncated = false
        let deadline = Date().addingTimeInterval(180)

        while outOpen || errOpen || !reaped {
            if !reaped {
                let waited = waitpid(pid, &status, WNOHANG)
                if waited == pid {
                    reaped = true
                }
            }
            if outOpen {
                let chunk = readChunk(outFD)
                out.append(chunk.data)
                outOpen = chunk.open
            }
            if errOpen {
                let chunk = readChunk(errFD)
                err.append(chunk.data)
                errOpen = chunk.open
            }
            if out.count + err.count > 300_000 {
                truncated = true
                if !reaped {
                    kill(pid, SIGKILL)
                    _ = waitpid(pid, &status, 0)
                    reaped = true
                }
                break
            }
            if Date() > deadline {
                timedOut = true
                if !reaped {
                    kill(pid, SIGKILL)
                    _ = waitpid(pid, &status, 0)
                    reaped = true
                }
                break
            }
            if !outOpen && !errOpen && reaped {
                break
            }
            var fds = [
                pollfd(fd: outOpen ? outFD : -1, events: Int16(POLLIN), revents: 0),
                pollfd(fd: errOpen ? errFD : -1, events: Int16(POLLIN), revents: 0),
            ]
            _ = fds.withUnsafeMutableBufferPointer { buffer in
                poll(buffer.baseAddress, nfds_t(buffer.count), 200)
            }
        }

        var text = ""
        if let stdout = String(data: out, encoding: .utf8), !stdout.isEmpty {
            text += stdout
        }
        if let stderr = String(data: err, encoding: .utf8), !stderr.isEmpty {
            if !text.isEmpty && !text.hasSuffix("\n") {
                text += "\n"
            }
            text += stderr
        }
        if text.isEmpty {
            text = "(no output)"
        }
        if truncated {
            text += "\n(output truncated)"
        }
        if timedOut {
            text += "\n(timed out — bounded at 180s)"
        }
        return (exitCode(status), text)
    }

    private static func readChunk(_ fd: Int32) -> (data: Data, open: Bool) {
        var buffer = [UInt8](repeating: 0, count: 8192)
        let count = buffer.withUnsafeMutableBytes { raw -> ssize_t in
            guard let base = raw.baseAddress else { return -1 }
            return Darwin.read(fd, base, raw.count)
        }
        if count > 0 {
            return (Data(buffer.prefix(Int(count))), true)
        }
        if count == 0 {
            return (Data(), false)
        }
        if errno == EAGAIN || errno == EWOULDBLOCK {
            return (Data(), true)
        }
        return (Data(), false)
    }

    private static func exitCode(_ status: Int32) -> Int32 {
        if status & 0x7F == 0 {
            return (status >> 8) & 0xFF
        }
        return status
    }
}
