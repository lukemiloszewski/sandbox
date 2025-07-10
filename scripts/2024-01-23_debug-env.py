import platform
import sys

import distutils


def debug_system():
    try:
        distutils_info = distutils.__version__
    except AttributeError:
        distutils_info = "distutils version information not available"

    # CPU info
    cpu_info = {
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        # "Cores (Physical)": psutil.cpu_count(logical=False),
        # "Cores (Logical)": psutil.cpu_count(logical=True),
    }

    # Python installation info
    python_info = {
        "Python Version": platform.python_version(),
        "Python Compiler": platform.python_compiler(),
        "Python Build": platform.python_build(),
        "Python Implementation": platform.python_implementation(),
        "Python Executable": sys.executable,
    }

    print("Distutils Info:", distutils_info)
    print("CPU Info:", cpu_info)
    print("Python Installation Info:", python_info)


if __name__ == "__main__":
    debug_system()
