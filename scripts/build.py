import os
import shutil
import subprocess
import concurrent.futures
import threading
import logging
import platform

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.getenv("GITHUB_STEP_SUMMARY"),
    format="%(message)s",
)

PLATFORM: str = os.getenv("PLATFORM")
GO_VERSION: str = os.getenv("GO_VERSION")

if not all([PLATFORM, GO_VERSION]):
    raise ValueError("Missing required environment variables")

log_lock = threading.Lock()


def is_m1():
    system = platform.system()
    architecture = platform.machine()
    if system == "Darwin" and architecture == "arm64":
        return True
    else:
        return False


options = {
    "buildmode": [("exe", ""), ("pie", "pie")],
    "strip": [
        ("", ""),
        ("-s -w", "strip"),
    ],
    "cgo": [
        (True, "cgo"),
        (False, ""),
    ],
    "arch": [
        "amd64",
        "arm64",
        "386",
    ],
}

if PLATFORM == "darwin":
    if is_m1():
        options["arch"] = [
            "arm64",
        ]
    else:
        options["arch"] = [
            "amd64",
            "386",
        ]

if PLATFORM == "windows":
    options["arch"] = [
        "amd64",
        "386",
    ]

go_binary = shutil.which("go")
if go_binary is None:
    raise FileNotFoundError("go binary not found in PATH")
go_binary = go_binary.replace("\\", "/")


def remove_empty_lines(s: str) -> str:
    return "\n".join(filter(None, s.split("\n")))


def render_env(env: dict) -> str:
    return "\n".join(f"{k}={v}" for k, v in env.items())

def render_args(args: list) -> str:
    new_args = []
    for arg in args:
        if " " in arg:
            arg = f'"{arg}"'
        new_args.append(arg)
    return " ".join(new_args)

cmd_env = os.environ.copy()


def build(
    buildmode: str, arch: str, ldflags: str, cgo: bool, output_suffix: str
) -> None:
    vers = int(GO_VERSION.split(".")[1])

    output = f"bin-{PLATFORM}-{GO_VERSION}-{arch}" + (
        f"-{output_suffix}" if output_suffix else ""
    )
    output = os.path.abspath(output).replace("\\", "/")

    args = [go_binary, "build", "-a", f"-buildmode={buildmode}", "-gcflags=-l"]

    if ldflags:
        args.append(ldflags)

    args.extend(["-o", output, "main.go"])

    env = dict()
    if not cgo:
        env["CGO_ENABLED"] = "0"
    else:
        env["CGO_ENABLED"] = "1"
        args.append("cgo.go")
        if vers >= 19:
            args.append("sqlite.go")
            with open("go.mod", "a") as f:
                f.write("require github.com/mattn/go-sqlite3 v1.14.22\n")

    env["GOARCH"] = arch
    env["GOOS"] = PLATFORM

    if vers >= 16:
        args.append("embed.go")

    # For windows, run with msys2
    if PLATFORM == "windows":
        args = ["msys2.cmd", "-c", render_args(args)]
        if arch == "amd64":
            env["MSYSTEM"] = "MINGW64"
            env["CC"] = "x86_64-w64-mingw32-gcc"
        elif arch == "386":
            env["MSYSTEM"] = "MINGW32"
            env["CC"] = "i686-w64-mingw32-gcc"

    if vers <= 10 and arch == "arm64":
        return

    if buildmode == "pie":
        if PLATFORM == "windows":
            if vers < 15:
                # Windows does not support PIE
                return

        if PLATFORM == "linux":
            if vers < 8:
                # Linux does not support PIE
                return

        if PLATFORM == "darwin":
            if vers < 10:
                # Darwin does not support PIE
                return

        if not cgo:
            # PIE requires cgo
            return

    if arch == "arm64":
        if PLATFORM == "windows":
            if vers < 16:
                # Windows does not support arm64
                return

    if arch == "386" and PLATFORM == "darwin":
        # 386 is not supported on macOS
        return

    if cgo:
        if PLATFORM == "darwin":
            if vers < 10:
                # have bug on new macOS
                return

        if PLATFORM == "linux":
            if vers < 6:
                # ld error
                return

    if is_m1() and cgo:
        if vers < 18:
            # a dwarf error, see https://github.com/golang/go/issues/53000
            return

    if PLATFORM == "linux" and arch == "arm64":
        env["CC"] = "aarch64-linux-gnu-gcc"

    full_env = {**cmd_env, **env}
    result = subprocess.run(
        args=args,
        capture_output=True,
        text=True,
        env=full_env,
    )
    if result.returncode != 0:
        print(f"Failed to build `{output}`")
        with log_lock:
            combined_output = result.stdout + "\n" + result.stderr
            logging.error(
                f"## {output} Failed\n"
                f"Command: `{result.args}`\n"
                f"Environment:\n"
                f"```\n{render_env(env)}\n```\n"
                f"```log\n{remove_empty_lines(combined_output)}\n```"
            )
    else:
        print(f"Built `{output}` successfully\n {' '.join(args)}")


def replace_string_in_file(file_path: str, old_string: str, new_string: str) -> None:
    try:
        # Open the file for reading
        with open(file_path, "r") as file:
            file_data = file.read()

        # Replace the string
        modified_data = file_data.replace(old_string, new_string)

        # Open the file for writing
        with open(file_path, "w") as file:
            file.write(modified_data)

        print(f"String '{old_string}' successfully replaced with '{new_string}'")
    except Exception as e:
        print(f"An error occurred: {e}")


# order: strip-ext-pie-cgo
def main() -> None:
    version = GO_VERSION
    verbit = version.split(".")[1]
    if int(verbit) < 16:
        replace_string_in_file("go.mod", "go 1.16", f"go {version}")

    for buildmode, buildmode_suffix in options["buildmode"]:
        for strip, strip_suffix in options["strip"]:
            for cgo, cgo_suffix in options["cgo"]:
                for arch in options["arch"]:
                    parts = filter(
                        None,
                        [
                            strip_suffix,
                            buildmode_suffix,
                            cgo_suffix,
                        ],
                    )
                    output_suffix = "-".join(parts)
                    ldflags = ""
                    if strip != "":
                        ldflags = f"-ldflags={strip}"
                    build(buildmode, arch, ldflags, cgo, output_suffix)

    for file in os.listdir("."):
        if os.path.isfile(file):
            print(file)


if __name__ == "__main__":
    main()
