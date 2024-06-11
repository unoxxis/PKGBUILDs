#!/usr/bin/env python3

# Script to list optional dependencies of installed packages
# Requires expac

# TODO Command Line options - installed / not installed / all with marker

import shutil
import subprocess
from functools import partial

class bcolors:
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def format_pkg_name(package: str, color: bool=False) -> str:
    if color:
        return f"{bcolors.BLUE}{package}{bcolors.ENDC}"
    return package

def format_pkg_description(description: str, color: bool=False) -> str:
    #if color:
    #    return description
    return description

def format_pkg_installed(installed: bool, color: bool=False) -> str:
    if color and installed:
        return f" {bcolors.CYAN}[Installed]{bcolors.ENDC}"
    if installed:
        return " [Installed]"
    return ""

def list_optdeps(list_mode: str = 'not-installed', color: bool = True) -> None:
    pacman_bin = shutil.which('pacman')
    expac_bin = shutil.which('expac')
    
    run_command = partial(subprocess.run, capture_output=True, check=True, text=True)
    fmt_pkg_name = partial(format_pkg_name, color=color)
    fmt_pkg_description = partial(format_pkg_description, color=color)
    fmt_pkg_installed = partial(format_pkg_installed, color=color)

    # Get all installed packages
    process_result = run_command([pacman_bin, '-Qq']).stdout.split('\n')
    installed_packages = set([pkg for pkg in process_result if pkg])

    # Loop over installed packages and collect their optional dependencies
    dependency_messages = dict()
    package_descriptions = dict()
    optdepend_packages = set()
    for package in installed_packages:
        # Get optional dependencies
        process_result = run_command([expac_bin, '-l', '\n', '%O', package]).stdout.split('\n')
        optdeps = {optdef.split(':')[0]: optdef.split(':', maxsplit=1)[1].lstrip() for optdef in process_result if optdef}
        #print(package, " > ", optdeps)

        for optdep_package in optdeps.keys():
            # Add package to set of optionally dependent packages
            optdepend_packages.add(optdep_package)
            # Add parent package to its dependencies
            if optdep_package not in dependency_messages:
                dependency_messages[optdep_package] = dict()
            dependency_messages[optdep_package][package] = optdeps[optdep_package]
            #if optdep_package not in package_descriptions:
            #    package_descriptions[optdep_package] = run_command([expac_bin, "-S", "%d", optdep_package]).stdout.strip()

        #if len(optdepend_packages) >= 10:
        #    break

    # Select which packages to show
    if list_mode == 'all':
        show_packages = optdepend_packages
    elif list_mode == 'installed':
        show_packages = optdepend_packages & installed_packages
    elif list_mode == 'not-installed':
        show_packages = optdepend_packages - installed_packages
    else:
        raise ValueError(f"Unknown {list_mode=}")

    # Get package descriptions
    process_result = run_command([expac_bin, "-S", "%n>%d"] + list(show_packages)).stdout.split("\n")
    package_descriptions = {pkg.split('>')[0]: pkg.split('>', maxsplit=1)[1].lstrip() for pkg in process_result if pkg}

    # Iterate over shown packages and list which other packages have them as optional dependency
    for package in sorted(show_packages):
        # Header
        print(
            fmt_pkg_name(package) + fmt_pkg_installed(run_command([pacman_bin, "-Q", package], check=False).returncode == 0)
            + "  " +fmt_pkg_description(package_descriptions.get(package, '(no desciption)'))
        )
        # Optional packages
        for reqpackage, optdescription in sorted(dependency_messages[package].items()):
            print(
                "  > " + fmt_pkg_name(reqpackage) + "  " + fmt_pkg_description(optdescription)                
            )

if __name__ == '__main__':
    list_optdeps(list_mode='not-installed')