/*
 * primula.exe for Windows: starts "python\python.exe -X utf8 -m primula <arguments>" from the
 * directory of this program and returns its exit code.
 *
 * Why not primula.cmd: a batch file is run through cmd.exe, which mangles arguments with
 * special characters and non-ASCII paths; a real executable passes the command line as is.
 * The standard handles are inherited, so the pipes of Primula Studio work unchanged.
 * Built by studio/windows/build-win.sh (x86_64-w64-mingw32-gcc -municode).
 */
#include <windows.h>
#include <wchar.h>
#include <stdlib.h>

/* Skip the program name (possibly quoted) at the start of the command line. */
static const wchar_t *after_program(const wchar_t *line)
{
    if (*line == L'"') {
        ++line;
        while (*line && *line != L'"') ++line;
        if (*line) ++line;
    } else {
        while (*line && *line != L' ' && *line != L'\t') ++line;
    }
    while (*line == L' ' || *line == L'\t') ++line;
    return line;
}

int wmain(void)
{
    wchar_t self[MAX_PATH * 2];
    DWORD length = GetModuleFileNameW(NULL, self, (DWORD)(sizeof self / sizeof self[0]));
    if (length == 0 || length >= sizeof self / sizeof self[0]) return 120;
    wchar_t *slash = wcsrchr(self, L'\\');
    if (!slash) return 120;
    *slash = 0;                                     /* self = directory of primula.exe */

    const wchar_t *rest = after_program(GetCommandLineW());
    size_t size = wcslen(self) + wcslen(rest) + 128;
    wchar_t *command = (wchar_t *)malloc(size * sizeof(wchar_t));
    if (!command) return 120;
    swprintf(command, size, L"\"%ls\\python\\python.exe\" -X utf8 -m primula %ls", self, rest);

    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    ZeroMemory(&startup, sizeof startup);
    startup.cb = sizeof startup;
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    /* The standard handles must be inheritable, or the child writes into the void (seen on
     * some Wine setups where a console handle is not). No CREATE_NO_WINDOW: the child shares
     * this process's console, so output reaches the terminal; when Studio starts this program
     * it already runs without a window, and the child inherits that. */
    HANDLE std[3] = { startup.hStdInput, startup.hStdOutput, startup.hStdError };
    for (int i = 0; i < 3; ++i)
        if (std[i] && std[i] != INVALID_HANDLE_VALUE)
            SetHandleInformation(std[i], HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
    if (!CreateProcessW(NULL, command, NULL, NULL, TRUE, 0, NULL, NULL, &startup, &process)) {
        free(command);
        return 121;                                 /* the bundled Python is missing */
    }
    free(command);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return (int)code;
}
