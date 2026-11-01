/* KernelLab.app soft UI.
 *
 * Arm64 Mach-O built without the iOS SDK. It is a UIKit shell:
 *   Console — posix_spawn /var/jb/usr/bin/kernellab (fixed argv) and show stdout
 *   Probes  — list .m/.h filenames under /var/jb/var/kernellab/probes
 *
 * It does not compile, run, or generate probe sources. The empty paste
 * stub is the comment block labeled for Kolby. APPLE-SUBMIT stays closed.
 * The SwiftUI sources under app/Sources are the Theos rebuild of this UI.
 */

typedef signed char BOOL;
typedef unsigned long NSUInteger;
typedef struct objc_object *id;
typedef struct objc_class *Class;
typedef struct objc_selector *SEL;
typedef void (*IMP)(void);

struct CGRect {
    double x;
    double y;
    double width;
    double height;
};

struct NSRange {
    unsigned long location;
    unsigned long length;
};

struct pollfd {
    int fd;
    short events;
    short revents;
};

typedef struct {
    id receiver;
    Class super_class;
} objc_super;

typedef struct _posix_spawn_file_actions *posix_spawn_file_actions_t;

extern void objc_msgSend(void);
extern void objc_msgSendSuper(void);
extern Class objc_getClass(const char *name);
extern SEL sel_registerName(const char *name);
extern Class objc_allocateClassPair(Class superclass, const char *name, unsigned long extra);
extern void objc_registerClassPair(Class cls);
extern int class_addMethod(Class cls, SEL name, IMP imp, const char *types);
extern Class object_getClass(id obj);
extern Class class_getSuperclass(Class cls);
extern void objc_setAssociatedObject(id object, const void *key, id value, unsigned long policy);
extern id objc_getAssociatedObject(id object, const void *key);
extern int UIApplicationMain(int argc, char **argv, id principal, id delegate_name);

extern int posix_spawn(int *pid, const char *path, posix_spawn_file_actions_t *actions, void *attr,
                        char *const argv[], char *const envp[]);
extern int posix_spawn_file_actions_init(posix_spawn_file_actions_t *actions);
extern int posix_spawn_file_actions_destroy(posix_spawn_file_actions_t *actions);
extern int posix_spawn_file_actions_adddup2(posix_spawn_file_actions_t *actions, int fd, int newfd);
extern int posix_spawn_file_actions_addclose(posix_spawn_file_actions_t *actions, int fd);
extern int pipe(int fds[2]);
extern int close(int fd);
extern long read(int fd, void *buf, unsigned long count);
extern int waitpid(int pid, int *status, int options);
extern int kill(int pid, int sig);
extern int poll(struct pollfd *fds, unsigned int nfds, int timeout);
extern int fcntl(int fd, int cmd, ...);
extern int access(const char *path, int mode);
extern int mkdir(const char *path, unsigned short mode);
extern int open(const char *path, int flags, ...);
extern long write(int fd, const void *buf, unsigned long count);
extern char *strerror(int err);
extern int *__error(void);
extern char **environ;
extern void *malloc(unsigned long size);
extern void free(void *ptr);
extern unsigned long strlen(const char *s);
extern int snprintf(char *str, unsigned long size, const char *fmt, ...);
extern int strcmp(const char *a, const char *b);

#define errno (*__error())

enum {
    OBJC_ASSOCIATION_RETAIN = 1,
    POLLIN = 0x0001,
    F_GETFL = 3,
    F_SETFL = 4,
    O_NONBLOCK = 0x0004,
    O_WRONLY = 0x0001,
    O_CREAT = 0x0200,
    O_EXCL = 0x0800,
    WNOHANG = 1,
    SIGKILL = 9,
    X_OK = 1,
    EAGAIN = 35,
    EEXIST = 17,
    STDOUT_FILENO = 1,
    STDERR_FILENO = 2
};

static const char *kProbes = "/var/jb/var/kernellab/probes";
static const char *kStubText =
    "// Kolby pastes\n"
    "// user-owned sources only\n"
    "// KernelLab does not compile or run this file.\n";
static const char kLogKey[] = "kernellab.log";
static const char kWindowKey[] = "kernellab.window";

static SEL sel(const char *name) {
    return sel_registerName(name);
}

static id cls(const char *name) {
    return (id)objc_getClass(name);
}

static id msg0(id obj, const char *name) {
    return ((id (*)(id, SEL))objc_msgSend)(obj, sel(name));
}

static id msg1(id obj, const char *name, id arg) {
    return ((id (*)(id, SEL, id))objc_msgSend)(obj, sel(name), arg);
}

static void msg1v(id obj, const char *name, id arg) {
    ((void (*)(id, SEL, id))objc_msgSend)(obj, sel(name), arg);
}

static id nsstr(const char *text) {
    if (text == 0) {
        text = "";
    }
    return ((id (*)(id, SEL, const char *))objc_msgSend)(cls("NSString"), sel("stringWithUTF8String:"), text);
}

static const char *utf8(id string) {
    if (string == 0) {
        return "";
    }
    const char *text = ((const char *(*)(id, SEL))objc_msgSend)(string, sel("UTF8String"));
    return text == 0 ? "" : text;
}

static struct CGRect bounds_of(id obj) {
    return ((struct CGRect (*)(id, SEL))objc_msgSend)(obj, sel("bounds"));
}

static void set_frame(id view, struct CGRect frame) {
    ((void (*)(id, SEL, struct CGRect))objc_msgSend)(view, sel("setFrame:"), frame);
}

static void set_text(id view, const char *text) {
    msg1v(view, "setText:", nsstr(text));
}

static void call_super(id self, const char *name) {
    objc_super sup;
    sup.receiver = self;
    sup.super_class = class_getSuperclass(object_getClass(self));
    ((void (*)(objc_super *, SEL))objc_msgSendSuper)(&sup, sel(name));
}

static int ends_with_source(const char *name) {
    unsigned long n = strlen(name);
    if (n < 3 || name[n - 2] != '.') {
        return 0;
    }
    char ext = name[n - 1];
    if (ext >= 'A' && ext <= 'Z') {
        ext = (char)(ext - 'A' + 'a');
    }
    return ext == 'm' || ext == 'h';
}

static int has_root_prefix(const char *path, const char *root) {
    unsigned long n = strlen(root);
    unsigned long i = 0;
    if (path == 0) {
        return 0;
    }
    while (i < n) {
        if (path[i] != root[i]) {
            return 0;
        }
        i++;
    }
    return path[n] == '\0' || path[n] == '/';
}

static void append_text(char *out, unsigned long cap, unsigned long *used, const char *text) {
    unsigned long i = 0;
    if (text == 0 || *used + 1 >= cap) {
        return;
    }
    while (text[i] != '\0' && *used + 1 < cap) {
        out[(*used)++] = text[i++];
    }
    out[*used] = '\0';
}

static void list_dir(id fm, id dir, const char *root, int depth, char *out, unsigned long cap, unsigned long *used, int *count) {
    id names;
    id sorted;
    unsigned long n;
    unsigned long i;
    if (depth > 8 || *count >= 500) {
        return;
    }
    names = ((id (*)(id, SEL, id, id *))objc_msgSend)(fm, sel("contentsOfDirectoryAtPath:error:"), dir, 0);
    if (names == 0) {
        return;
    }
    sorted = ((id (*)(id, SEL, SEL))objc_msgSend)(names, sel("sortedArrayUsingSelector:"), sel("compare:"));
    if (sorted == 0) {
        sorted = names;
    }
    n = ((unsigned long (*)(id, SEL))objc_msgSend)(sorted, sel("count"));
    for (i = 0; i < n; i++) {
        id name;
        id child;
        id resolved;
        const char *leaf;
        const char *full;
        BOOL is_dir = 0;
        if (*count >= 500) {
            append_text(out, cap, used, "(listing stopped at 500 names)\n");
            return;
        }
        name = ((id (*)(id, SEL, unsigned long))objc_msgSend)(sorted, sel("objectAtIndex:"), i);
        leaf = utf8(name);
        if (leaf[0] == '\0' || leaf[0] == '.') {
            continue;
        }
        child = ((id (*)(id, SEL, id))objc_msgSend)(dir, sel("stringByAppendingPathComponent:"), name);
        resolved = msg0(child, "stringByResolvingSymlinksInPath");
        full = utf8(resolved);
        if (!has_root_prefix(full, root)) {
            continue;
        }
        ((BOOL (*)(id, SEL, id, BOOL *))objc_msgSend)(fm, sel("fileExistsAtPath:isDirectory:"), resolved, &is_dir);
        if (is_dir) {
            list_dir(fm, resolved, root, depth + 1, out, cap, used, count);
            continue;
        }
        if (!ends_with_source(leaf)) {
            continue;
        }
        if (has_root_prefix(full, root) && full[strlen(root)] == '/') {
            append_text(out, cap, used, full + strlen(root) + 1);
        } else {
            append_text(out, cap, used, leaf);
        }
        append_text(out, cap, used, "\n");
        (*count)++;
    }
}

static void format_probe_list(char *out, unsigned long cap) {
    id fm;
    id root;
    BOOL is_dir = 0;
    int count = 0;
    unsigned long used = 0;
    out[0] = '\0';
    append_text(out, cap, &used, "Probes\n");
    append_text(out, cap, &used, kProbes);
    append_text(out, cap, &used, "\nNames only. KernelLab does not compile or run these files.\n");
    append_text(out, cap, &used, "Kolby pastes.\n");
    append_text(out, cap, &used, "future: operator-supplied runner / codegen plugs here — authored by Kolby, not shipped.\n\n");
    fm = msg0(cls("NSFileManager"), "defaultManager");
    root = nsstr(kProbes);
    ((BOOL (*)(id, SEL, id, BOOL *))objc_msgSend)(fm, sel("fileExistsAtPath:isDirectory:"), root, &is_dir);
    if (!is_dir) {
        append_text(out, cap, &used, "Folder is not on disk yet. Drop .m and .h files with Filza, then Refresh.\n");
        return;
    }
    list_dir(fm, root, kProbes, 0, out, cap, &used, &count);
    if (count == 0) {
        append_text(out, cap, &used, "No .m or .h files in this folder.\n");
    }
}

static void ensure_dir(const char *path) {
    char buf[256];
    unsigned long n = 0;
    unsigned long i;
    if (mkdir(path, 0755) == 0 || errno == EEXIST) {
        return;
    }
    n = strlen(path);
    if (n >= sizeof buf) {
        return;
    }
    for (i = 0; i < n; i++) {
        buf[i] = path[i];
        if (path[i] == '/' && i > 0) {
            buf[i] = '\0';
            if (mkdir(buf, 0755) != 0 && errno != EEXIST) {
                return;
            }
            buf[i] = '/';
        }
    }
    mkdir(path, 0755);
}

static int write_new_file(const char *path, const char *text) {
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0644);
    unsigned long n;
    long wrote;
    if (fd < 0) {
        return fd;
    }
    n = strlen(text);
    wrote = write(fd, text, n);
    close(fd);
    return wrote == (long)n ? 0 : -1;
}

static void write_empty_stubs(char *out, unsigned long cap) {
    char path[256];
    const char *names[] = {"kolby.m", "kolby.h"};
    unsigned long i;
    unsigned long used = 0;
    out[0] = '\0';
    ensure_dir(kProbes);
    append_text(out, cap, &used, "Kolby pastes. Empty stub only.\n");
    for (i = 0; i < 2; i++) {
        snprintf(path, sizeof path, "%s/%s", kProbes, names[i]);
        if (write_new_file(path, kStubText) == 0) {
            append_text(out, cap, &used, "Wrote ");
            append_text(out, cap, &used, path);
            append_text(out, cap, &used, "\n");
        } else if (errno == EEXIST) {
            append_text(out, cap, &used, "Left existing ");
            append_text(out, cap, &used, path);
            append_text(out, cap, &used, "\n");
        } else {
            append_text(out, cap, &used, "Could not write ");
            append_text(out, cap, &used, path);
            append_text(out, cap, &used, "\n");
        }
    }
    append_text(out, cap, &used, "KernelLab does not compile or run it.\n");
}

static const char *resolve_cli(void) {
    const char *bins[] = {"/var/jb/usr/bin/kernellab", "/usr/bin/kernellab"};
    unsigned long i;
    for (i = 0; i < 2; i++) {
        if (access(bins[i], X_OK) == 0) {
            return bins[i];
        }
    }
    for (i = 0; i < 2; i++) {
        if (access(bins[i], 0) == 0) {
            return bins[i];
        }
    }
    return 0;
}

static int exit_code(int status) {
    if ((status & 0x7f) == 0) {
        return (status >> 8) & 0xff;
    }
    return status;
}

static void run_lab(char *out, unsigned long cap, const char **args) {
    const char *bin;
    char *argv[8];
    int out_pipe[2] = {-1, -1};
    int err_pipe[2] = {-1, -1};
    posix_spawn_file_actions_t actions = 0;
    int pid = 0;
    int spawned;
    int i;
    unsigned long used = 0;
    int out_open = 1;
    int err_open = 1;
    int reaped = 0;
    int status = 0;
    int ticks = 0;
    out[0] = '\0';
    bin = resolve_cli();
    append_text(out, cap, &used, "$ kernellab");
    for (i = 0; args[i] != 0; i++) {
        append_text(out, cap, &used, " ");
        append_text(out, cap, &used, args[i]);
    }
    append_text(out, cap, &used, "\n");
    if (bin == 0) {
        append_text(out, cap, &used, "kernellab CLI not found. Expected /var/jb/usr/bin/kernellab.\n");
        return;
    }
    argv[0] = (char *)bin;
    for (i = 0; args[i] != 0 && i < 6; i++) {
        argv[i + 1] = (char *)args[i];
    }
    argv[i + 1] = 0;
    if (pipe(out_pipe) != 0 || pipe(err_pipe) != 0) {
        append_text(out, cap, &used, "Could not create pipes for kernellab.\n");
        return;
    }
    posix_spawn_file_actions_init(&actions);
    posix_spawn_file_actions_adddup2(&actions, out_pipe[1], STDOUT_FILENO);
    posix_spawn_file_actions_adddup2(&actions, err_pipe[1], STDERR_FILENO);
    posix_spawn_file_actions_addclose(&actions, out_pipe[0]);
    posix_spawn_file_actions_addclose(&actions, err_pipe[0]);
    posix_spawn_file_actions_addclose(&actions, out_pipe[1]);
    posix_spawn_file_actions_addclose(&actions, err_pipe[1]);
    spawned = posix_spawn(&pid, bin, &actions, 0, argv, environ);
    posix_spawn_file_actions_destroy(&actions);
    close(out_pipe[1]);
    close(err_pipe[1]);
    if (spawned != 0) {
        append_text(out, cap, &used, "Could not start kernellab (");
        append_text(out, cap, &used, strerror(spawned));
        append_text(out, cap, &used, ").\n");
        close(out_pipe[0]);
        close(err_pipe[0]);
        return;
    }
    fcntl(out_pipe[0], F_SETFL, fcntl(out_pipe[0], F_GETFL) | O_NONBLOCK);
    fcntl(err_pipe[0], F_SETFL, fcntl(err_pipe[0], F_GETFL) | O_NONBLOCK);
    while (out_open || err_open || !reaped) {
        char buf[1024];
        struct pollfd fds[2];
        long nread;
        if (!reaped && waitpid(pid, &status, WNOHANG) == pid) {
            reaped = 1;
        }
        if (out_open) {
            nread = read(out_pipe[0], buf, sizeof buf - 1);
            if (nread > 0) {
                buf[nread] = '\0';
                append_text(out, cap, &used, buf);
            } else if (nread == 0) {
                out_open = 0;
            } else if (errno != EAGAIN) {
                out_open = 0;
            }
        }
        if (err_open) {
            nread = read(err_pipe[0], buf, sizeof buf - 1);
            if (nread > 0) {
                buf[nread] = '\0';
                append_text(out, cap, &used, buf);
            } else if (nread == 0) {
                err_open = 0;
            } else if (errno != EAGAIN) {
                err_open = 0;
            }
        }
        if (used + 64 >= cap) {
            append_text(out, cap, &used, "\n(output truncated)\n");
            if (!reaped) {
                kill(pid, SIGKILL);
                waitpid(pid, &status, 0);
                reaped = 1;
            }
            break;
        }
        if (ticks > 100) {
            append_text(out, cap, &used, "\n(timed out)\n");
            if (!reaped) {
                kill(pid, SIGKILL);
                waitpid(pid, &status, 0);
                reaped = 1;
            }
            break;
        }
        if (!out_open && !err_open && reaped) {
            break;
        }
        fds[0].fd = out_open ? out_pipe[0] : -1;
        fds[0].events = POLLIN;
        fds[0].revents = 0;
        fds[1].fd = err_open ? err_pipe[0] : -1;
        fds[1].events = POLLIN;
        fds[1].revents = 0;
        poll(fds, 2, 200);
        ticks++;
    }
    close(out_pipe[0]);
    close(err_pipe[0]);
    if (reaped) {
        char line[64];
        snprintf(line, sizeof line, "exit %d\n", exit_code(status));
        append_text(out, cap, &used, line);
    }
}

static id log_view(id self) {
    return objc_getAssociatedObject(self, kLogKey);
}

static void show(id self, const char *text) {
    id view = log_view(self);
    if (view != 0) {
        set_text(view, text);
    }
}

static id make_log(id self, struct CGRect frame) {
    id view = msg0(cls("UITextView"), "new");
    id font = ((id (*)(id, SEL, double))objc_msgSend)(cls("UIFont"), sel("systemFontOfSize:"), 14.0);
    id bg = ((id (*)(id, SEL, double, double, double, double))objc_msgSend)(
        cls("UIColor"), sel("colorWithRed:green:blue:alpha:"), 0.05, 0.07, 0.11, 1.0);
    id fg = msg0(cls("UIColor"), "whiteColor");
    set_frame(view, frame);
    msg1v(view, "setFont:", font);
    msg1v(view, "setBackgroundColor:", bg);
    msg1v(view, "setTextColor:", fg);
    ((void (*)(id, SEL, BOOL))objc_msgSend)(view, sel("setEditable:"), 0);
    objc_setAssociatedObject(self, kLogKey, view, OBJC_ASSOCIATION_RETAIN);
    return view;
}

static id make_button(id target, const char *title, const char *action, struct CGRect frame) {
    id button = ((id (*)(id, SEL, unsigned long))objc_msgSend)(cls("UIButton"), sel("buttonWithType:"), 1);
    set_frame(button, frame);
    ((void (*)(id, SEL, id, unsigned long))objc_msgSend)(button, sel("setTitle:forState:"), nsstr(title), 0);
    ((void (*)(id, SEL, id, SEL, unsigned long))objc_msgSend)(
        button, sel("addTarget:action:forControlEvents:"), target, sel(action), 64);
    return button;
}

static void add_buttons(id self, id view, double y, double width, const char **titles, const char **actions, int count) {
    int i;
    double col_w = (width - 36.0) / 2.0;
    for (i = 0; i < count; i++) {
        int col = i % 2;
        int row = i / 2;
        struct CGRect frame;
        frame.x = 12.0 + col * (col_w + 12.0);
        frame.y = y + row * 48.0;
        frame.width = col_w;
        frame.height = 40.0;
        msg1v(view, "addSubview:", make_button(self, titles[i], actions[i], frame));
    }
}

static void paint_background(id view) {
    id color = ((id (*)(id, SEL, double, double, double, double))objc_msgSend)(
        cls("UIColor"), sel("colorWithRed:green:blue:alpha:"), 0.03, 0.04, 0.07, 1.0);
    msg1v(view, "setBackgroundColor:", color);
}

static void console_view_did_load(id self, SEL _cmd) {
    id view = msg0(self, "view");
    struct CGRect b = bounds_of(view);
    struct CGRect log_frame;
    const char *titles[] = {
        "List caches", "26.5 vs 27.0", "27.0 vs 26.5", "Diff", "Sim ident", "Show gate", "Tables"
    };
    const char *actions[] = {
        "runList:", "runTrain265:", "runTrain270:", "runDiff:", "runIdent:", "runGate:", "runTables:"
    };
    call_super(self, "viewDidLoad");
    msg1v(self, "setTitle:", nsstr("Console"));
    paint_background(view);
    log_frame.x = 12;
    log_frame.y = 16;
    log_frame.width = b.width - 24;
    log_frame.height = b.height * 0.46;
    if (log_frame.height < 160) {
        log_frame.height = 160;
    }
    msg1v(view, "addSubview:", make_log(self, log_frame));
    set_text(log_view(self),
             "KernelLab\n"
             "App shell over /var/jb/usr/bin/kernellab.\n"
             "klconsole stays at http://127.0.0.1:8737.\n"
             "APPLE-SUBMIT stays closed.\n"
             "This app does not ship kernel caches.\n");
    add_buttons(self, view, log_frame.y + log_frame.height + 12, b.width, titles, actions, 7);
}

static void show_lab(id self, const char **args) {
    char *out = (char *)malloc(180000);
    if (out == 0) {
        return;
    }
    run_lab(out, 180000, args);
    show(self, out);
    free(out);
}

static void run_list(id self, SEL _cmd, id sender) {
    const char *args[] = {"target", "list", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_train265(id self, SEL _cmd, id sender) {
    const char *args[] = {"target", "set", "--train", "26.5", "--baseline-train", "27.0", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_train270(id self, SEL _cmd, id sender) {
    const char *args[] = {"target", "set", "--train", "27.0", "--baseline-train", "26.5", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_diff(id self, SEL _cmd, id sender) {
    const char *args[] = {"diff", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_ident(id self, SEL _cmd, id sender) {
    const char *args[] = {"sim", "ident", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_gate(id self, SEL _cmd, id sender) {
    const char *args[] = {"gate", 0};
    (void)sender;
    show_lab(self, args);
}

static void run_tables(id self, SEL _cmd, id sender) {
    const char *args[] = {"tables", 0};
    (void)sender;
    show_lab(self, args);
}

static void probes_view_did_load(id self, SEL _cmd) {
    id view = msg0(self, "view");
    struct CGRect b = bounds_of(view);
    struct CGRect log_frame;
    char *out;
    const char *titles[] = {"Refresh", "Empty stub"};
    const char *actions[] = {"runRefresh:", "runStub:"};
    call_super(self, "viewDidLoad");
    msg1v(self, "setTitle:", nsstr("Probes"));
    paint_background(view);
    log_frame.x = 12;
    log_frame.y = 16;
    log_frame.width = b.width - 24;
    log_frame.height = b.height * 0.62;
    if (log_frame.height < 180) {
        log_frame.height = 180;
    }
    msg1v(view, "addSubview:", make_log(self, log_frame));
    out = (char *)malloc(120000);
    if (out != 0) {
        format_probe_list(out, 120000);
        set_text(log_view(self), out);
        free(out);
    }
    add_buttons(self, view, log_frame.y + log_frame.height + 12, b.width, titles, actions, 2);
}

static void run_refresh(id self, SEL _cmd, id sender) {
    char *out = (char *)malloc(120000);
    (void)sender;
    if (out == 0) {
        return;
    }
    format_probe_list(out, 120000);
    show(self, out);
    free(out);
}

static void run_stub(id self, SEL _cmd, id sender) {
    char note[512];
    char *out = (char *)malloc(120000);
    (void)sender;
    write_empty_stubs(note, sizeof note);
    if (out == 0) {
        show(self, note);
        return;
    }
    format_probe_list(out, 120000);
    {
        char *joined = (char *)malloc(120000);
        unsigned long used = 0;
        if (joined != 0) {
            joined[0] = '\0';
            append_text(joined, 120000, &used, note);
            append_text(joined, 120000, &used, "\n");
            append_text(joined, 120000, &used, out);
            show(self, joined);
            free(joined);
        }
    }
    free(out);
}

static BOOL did_finish(id self, SEL _cmd, id application, id options) {
    id screen;
    id window;
    id tabs;
    id console;
    id probes;
    id pair[2];
    id controllers;
    struct CGRect frame;
    (void)application;
    (void)options;
    screen = msg0(cls("UIScreen"), "mainScreen");
    frame = bounds_of(screen);
    window = msg0(cls("UIWindow"), "new");
    set_frame(window, frame);
    tabs = msg0(cls("UITabBarController"), "new");
    console = msg0(msg0((id)objc_getClass("KLConsoleController"), "alloc"), "init");
    probes = msg0(msg0((id)objc_getClass("KLProbesController"), "alloc"), "init");
    pair[0] = console;
    pair[1] = probes;
    controllers = ((id (*)(id, SEL, id *, unsigned long))objc_msgSend)(
        cls("NSArray"), sel("arrayWithObjects:count:"), pair, 2);
    ((void (*)(id, SEL, id, BOOL))objc_msgSend)(tabs, sel("setViewControllers:animated:"), controllers, 0);
    msg1v(window, "setRootViewController:", tabs);
    msg0(window, "makeKeyAndVisible");
    objc_setAssociatedObject(self, kWindowKey, window, OBJC_ASSOCIATION_RETAIN);
    return 1;
}

static void register_controller(const char *name, IMP view_did_load, const char **actions, IMP *imps, int count) {
    Class klass = objc_allocateClassPair(objc_getClass("UIViewController"), name, 0);
    int i;
    class_addMethod(klass, sel("viewDidLoad"), view_did_load, "v@:");
    for (i = 0; i < count; i++) {
        class_addMethod(klass, sel(actions[i]), imps[i], "v@:@");
    }
    objc_registerClassPair(klass);
}

int main(int argc, char **argv) {
    Class delegate;
    const char *console_actions[] = {
        "runList:", "runTrain265:", "runTrain270:", "runDiff:", "runIdent:", "runGate:", "runTables:"
    };
    IMP console_imps[] = {
        (IMP)run_list, (IMP)run_train265, (IMP)run_train270, (IMP)run_diff,
        (IMP)run_ident, (IMP)run_gate, (IMP)run_tables
    };
    const char *probe_actions[] = {"runRefresh:", "runStub:"};
    IMP probe_imps[] = {(IMP)run_refresh, (IMP)run_stub};
    id name;
    if (objc_getClass("UIResponder") == 0 || objc_getClass("UIViewController") == 0) {
        return 1;
    }
    register_controller("KLConsoleController", (IMP)console_view_did_load, console_actions, console_imps, 7);
    register_controller("KLProbesController", (IMP)probes_view_did_load, probe_actions, probe_imps, 2);
    delegate = objc_allocateClassPair(objc_getClass("UIResponder"), "KLAppDelegate", 0);
    class_addMethod(delegate, sel("application:didFinishLaunchingWithOptions:"), (IMP)did_finish, "B@:@@");
    objc_registerClassPair(delegate);
    name = nsstr("KLAppDelegate");
    return UIApplicationMain(argc, argv, 0, name);
}
