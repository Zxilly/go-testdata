import os
import subprocess
import concurrent.futures
import threading
from typing import Mapping


PLATFORM: str = os.getenv("PLATFORM")
GO_VERSION: str = os.getenv("GO_VERSION")
ARCH: str = os.getenv("ARCH")

cmd_env: Mapping[str, str] = {
    "GOOS": PLATFORM,
    "GOARCH": ARCH,
}

write_lock = threading.Lock()

options = {
    "buildmode": [("exe", ""), ("pie", "pie")],
    "strip": [
        ("", ""),
        ("-s -w", "strip"),
    ],
    "external": [
        ("", ""),
        ("-linkmode external", "ext"),
    ],
    "cgo": [True, False],
}


def build(buildmode: str, ldflags: str, cgo: bool, output_suffix: str) -> None:
    output = f"bin-{PLATFORM}-{GO_VERSION}-{ARCH}" + (f"-{output_suffix}" if output_suffix else "")
    command = rf"go build -a -buildmode={buildmode} {output} {ldflags} -o  ."

    env = cmd_env.copy()
    if not cgo:
        env["CGO_ENABLED"] = "0"
    else:
        env["CGO_ENABLED"] = "1"

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        with write_lock:
            with open(os.getenv("GITHUB_STEP_SUMMARY"), "a") as file:
                combined_output = result.stdout + "\n" + result.stderr
                file.write(f"Failed to build {output}:\n```log\n{combined_output}\n```\n")


# order: strip-ext-pie-cgo
def main() -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for buildmode, buildmode_suffix in options["buildmode"]:
            for strip, strip_suffix in options["strip"]:
                for external, external_suffix in options["external"]:
                    for cgo in options["cgo"]:
                        parts = filter(None, [strip_suffix, external_suffix, buildmode_suffix])
                        output_suffix = (
                            "-".join(parts)
                        )

                        ldflags = ""

                        if strip != "" or external != "":
                            ldflags = f'-ldflags="{" ".join([strip, external])}"'

                        if cgo:
                            output_suffix += "-cgo"

                        futures.append(
                            executor.submit(
                                build, buildmode, ldflags, cgo, output_suffix
                            )
                        )

        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
