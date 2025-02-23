"""
Builds the README.md file using the configuration
Markdown template and OpenAI API language models.
"""

import subprocess
import tempfile
from pathlib import Path

import git
import pandas as pd

from file_factory import FileHandler
from logger import Logger

LOGGER = Logger("readmeai_logger")


def build(
    conf: object, conf_helper: object, dependencies: list, df: pd.DataFrame
) -> None:
    """
    Main function to build the README.md file using the provided configuration,
    dependencies, and data. This function formats the content and saves it to file.

    Parameters
    ----------
    conf : object
        Configuration object containing GitHub and markdown configurations.
    conf_helper : object
        Configuration helper object containing file extensions and setup guides.
    dependencies : list
        List of project dependencies.
    df : pd.DataFrame
        DataFrame containing parsed information from project files.
    """

    name = conf.github.name
    url = conf.github.path

    md_file = conf.md.head
    md_close = conf.md.close
    md_intro = conf.md.intro
    md_dropdown = conf.md.dropdown
    md_modules = conf.md.modules
    md_setup = conf.md.setup
    md_slogan = conf.md.slogan.strip('"')
    md_toc = conf.md.toc
    md_tree = conf.md.tree

    cwd_path = Path.cwd()
    handler = FileHandler()
    json_path = cwd_path / conf.paths.badges
    json_dict = handler.read(json_path)

    df_cleaned = parse_pandas_cols(df)
    md_badges = get_badges(json_dict, dependencies)
    md_tables = create_tables(df_cleaned, md_dropdown)
    md_repo = create_directory_tree(url)
    md_setup = create_setup_guide(conf, conf_helper, df_cleaned)
    md_file = md_file.format(name, md_slogan, md_badges)
    md_file = f"{md_file}{md_toc}{md_intro}{md_tree}{md_repo}"
    md_file = f"{md_file}{md_modules}{md_tables}{md_setup}{md_close}"

    md_path = cwd_path / conf.paths.md
    handler.write(md_path, md_file)

    LOGGER.info(f"README.md file created at: {md_path}")


def get_badges(data: dict, dependencies: list) -> str:
    """
    Generates badge icons for each dependency in the project.

    Parameters
    ----------
    data : dict
        Dictionary containing available icons and their src.
    dependencies : list
        List of project dependencies.

    Returns
    -------
    str
        Formatted string containing badge icons for dependencies.
    """
    badges = []
    icons_dict = {icon["name"].lower(): icon["src"] for icon in data["icons"]}
    for dep in dependencies:
        if dep.lower() in icons_dict:
            badges.append(icons_dict[dep.lower()])
    return format_badges(badges, dependencies)


def format_badges(badges: list, dependencies: list) -> str:
    """
    Formats the badges into a string with a maximum of 8 badges per line.

    Parameters
    ----------
    badges : list
        List of badge icons.
    dependencies : list
        List of project dependencies.

    Returns
    -------
    str
        Formatted string with badge icons arranged.
    """
    badge_lines = []
    total_badges = len(badges)
    if total_badges < 8:
        badges_per_line = total_badges
    else:
        badges_per_line = total_badges // 2 + (total_badges % 2)

    if badges_per_line == 0:
        return ""

    for i in range(0, total_badges, badges_per_line):
        line = "\n".join(
            [
                f'<img src="{badge}" alt="{dep}" />'
                for dep, badge in zip(
                    dependencies[i : i + badges_per_line],
                    badges[i : i + badges_per_line],
                )
            ]
        )
        badge_lines.append(line)

    return "\n\n".join([f"{line}" for line in badge_lines])


def create_setup_guide(conf: object, conf_helper: object, df: pd.DataFrame):
    """
    Creates a setup guide for the project based on the top used language.

    Parameters
    ----------
    conf : object
        Configuration object containing GitHub and markdown configurations.
    conf_helper : object
        Configuration helper object containing file extensions and setup guides.
    df : pd.DataFrame
        DataFrame containing parsed information from project files.

    Returns
    -------
    str
        Formatted string with setup guide.
    """
    install_guide = "[INSERT-INSTALL-GUIDE-HERE]"
    run_guide = "[INSERT-RUN-GUIDE-HERE]"

    ignore_files = conf_helper.ignore_files
    name = conf.github.name
    path = conf.github.path

    df["Language"] = df["Module"].apply(
        lambda x: Path(x).suffix[1:] if Path(x).suffix[1:] not in ignore_files else None
    )
    top_language = df["Language"].value_counts().idxmax()

    try:
        language_name = conf_helper.file_extensions[top_language]
        language_setup = conf_helper.setup[language_name]

        LOGGER.info(f"Top project language: {top_language}")
        LOGGER.info(f"Top project language name: {language_name}")
        LOGGER.info(f"{language_name} installation and setup: {language_setup}")

        if language_setup:
            install_guide = language_setup[0]
            run_guide = language_setup[1]

    except KeyError as ke:
        LOGGER.warning(f"KeyError: {ke}. Using default install and run guides.")

    md_setup_guide = conf.md.setup.format(
        name, path, name, install_guide, name, run_guide
    )

    return md_setup_guide


def create_directory_tree(url: str) -> str:
    """
    Creates a directory tree structure of the project based on its repository URL.

    Parameters
    ----------
    url : str
        URL of the project's GitHub repository.

    Returns
    -------
    str
        Formatted string representing the project's directory tree structure.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "repo"

        try:
            git.Repo.clone_from(url, repo_path)
            tree_bytes = subprocess.check_output(["tree", "-n", repo_path])
            tree_str = tree_bytes.decode("utf-8")
            tree_lines = tree_str.split("\n")[1:]
            tree_str = "\n".join(tree_lines)
            tree_md = f"```bash\n{repo_path.name}\n{tree_str}```"
            return tree_md

        except git.exc.GitCommandError as e:
            LOGGER.warning(f"Error cloning repository: {e}")
            return ""

        except subprocess.CalledProcessError as e:
            LOGGER.warning(f"Error running 'tree' command: {e}")
            return ""

        except Exception as e:
            LOGGER.warning(f"Error creating directory tree: {e}")
            return ""


def create_tables(df: pd.DataFrame, dropdown: str) -> str:
    """
    Creates markdown tables for each sub-directory in the project.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing parsed information from project files.
    dropdown : str
        Markdown template for a dropdown menu.

    Returns
    -------
    str
        Formatted string with markdown tables for each sub-directory.
    """
    df["Sub-Directory"] = df["Module"].apply(
        lambda x: str(x).split("/")[-2].capitalize() if "/" in str(x) else "Root"
    )
    groups = df.groupby("Sub-Directory")
    tables = [
        group[["File", "Summary", "Module"]].to_markdown(index=False)
        for _, group in groups
    ]
    table_wrappers = [
        dropdown.format(sub_dir_name, table)
        for sub_dir_name, table in zip(groups.groups.keys(), tables)
    ]
    return "\n".join(table_wrappers)


def parse_pandas_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the DataFrame by extracting file and directory information from the 'Module' column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing parsed information from project files.

    Returns
    -------
    pd.DataFrame
        Processed DataFrame with additional columns.
    """
    df["Directory"] = df["Module"].apply(lambda x: str(Path(x).parent))
    df["File"] = df["Module"].apply(lambda x: str(Path(x).name))
    return df
