import os
import subprocess
import concurrent.futures
import threading
from typing import Mapping


PLATFORM: str = os.getenv("PLATFORM")
GO_VERSION: str = os.getenv("GO_VERSION")
ARCH: str = os.getenv("ARCH")
CGO: str = os.getenv("CGO")

cmd_env: Mapping[str, str] = {
    "GOOS": PLATFORM,
    "GOARCH": ARCH,
}

if CGO == "":
    cmd_env["CGO_ENABLED"] = "0"
else:
    cmd_env["CGO_ENABLED"] = "1"

write_lock = threading.Lock()


def build(buildmode: str, ldflags: str, output_suffix: str) -> None:
    output = f"bin-{PLATFORM}-{GO_VERSION}-{ARCH}-{output_suffix}{CGO}"
    command = rf"go build -a -buildmode={buildmode} {output} {ldflags} -o  ."
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, env=cmd_env
    )
    if result.returncode != 0:
        with write_lock:
            with open(os.getenv("GITHUB_STEP_SUMMARY"), "a") as file:
                combined_output = result.stdout + "\n" + result.stderr
                file.write("Failed to build " + output + "\n" + combined_output)


def main() -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(build, "exe", "", ""),
            executor.submit(build, "exe", '-ldflags="-s -w"', "strip"),
            executor.submit(build, "pie", "", "pie"),
            executor.submit(build, "pie", '-ldflags="-s -w"', "strip-pie"),
            executor.submit(build, "exe", '-ldflags="-linkmode external"', "ext"),
            executor.submit(
                build, "exe", '-ldflags="-s -w -linkmode external"', "strip-ext"
            ),
            executor.submit(build, "pie", '-ldflags="-linkmode external"', "ext-pie"),
            executor.submit(
                build, "pie", '-ldflags="-s -w -linkmode external"', "strip-ext-pie"
            ),
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
