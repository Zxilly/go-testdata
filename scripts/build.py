import os
import shutil
import subprocess
import concurrent.futures
import threading
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.getenv("GITHUB_STEP_SUMMARY"),
    format="%(message)s",
)

PLATFORM: str = os.getenv("PLATFORM")
GO_VERSION: str = os.getenv("GO_VERSION")
ARCH: str = os.getenv("ARCH")

if not all([PLATFORM, GO_VERSION, ARCH]):
    raise ValueError("Missing required environment variables")

cmd_env = os.environ.copy()
cmd_env.update(
    {
        "GOOS": PLATFORM,
        "GOARCH": ARCH,
    }
)

log_lock = threading.Lock()

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
}

go_binary = shutil.which("go")
if go_binary is None:
    raise FileNotFoundError("go binary not found in PATH")


def remove_empty_lines(s: str) -> str:
    return "\n".join(filter(None, s.split("\n")))


def build(buildmode: str, ldflags: str, cgo: bool, output_suffix: str) -> None:
    output = f"bin-{PLATFORM}-{GO_VERSION}-{ARCH}" + (
        f"-{output_suffix}" if output_suffix else ""
    )
    args = [go_binary, "build", "-a", f"-buildmode={buildmode}"]
    if ldflags:
        args.append(ldflags)
    args.extend(["-o", output, "."])

    env = cmd_env.copy()
    if not cgo:
        env["CGO_ENABLED"] = "0"
    else:
        env["CGO_ENABLED"] = "1"

    vers = int(GO_VERSION.split(".")[1])

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

    if cgo:
        if PLATFORM == "darwin":
            if vers < 10:
                # have bug on new macOS
                return

        if PLATFORM == "linux":
            if vers < 6:
                # ld error
                return

    result = subprocess.run(
        args=args,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        with log_lock:
            combined_output = result.stdout + "\n" + result.stderr
            logging.error(
                f"Failed to build `{output}`:\n"
                f"Command: `{result.args}`\n"
                f"CGO_ENABLED: `{env['CGO_ENABLED']}`\n"
                f"```log\n{remove_empty_lines(combined_output)}\n```\n"
            )
    else:
        print(f"Built `{output}` successfully\n")


# order: strip-ext-pie-cgo
def main() -> None:
    worker_count = os.cpu_count()
    if PLATFORM == "windows":
        worker_count = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = []

        for buildmode, buildmode_suffix in options["buildmode"]:
            for strip, strip_suffix in options["strip"]:
                for cgo, cgo_suffix in options["cgo"]:
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
                        ldflags = f'-ldflags={strip}'

                    futures.append(
                        executor.submit(build, buildmode, ldflags, cgo, output_suffix)
                    )

        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
