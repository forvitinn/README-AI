"""File i/o factory module for handling different file types."""

import json

import toml


class FileHandler:
    def __init__(self):
        self.file_actions = {
            "md": {"read": self.read_markdown, "write": self.write_markdown},
            "toml": {"read": self.read_toml, "write": self.write_toml},
            "json": {"read": self.read_json, "write": self.write_json},
        }
        self.cache = {}

    def read(self, file_path):
        """Reads the content of a file."""
        if file_path in self.cache:
            return self.cache[file_path]

        try:
            file_extension = str(file_path).split(".")[-1]
            reader = self.get_action(file_extension, "read")
            content = reader(file_path)
            self.cache[file_path] = content
            return content
        except Exception as e:
            print(f"Failed to read file {file_path}: {e}")
            return None

    def write(self, file_path, content):
        """Writes the content to a file."""
        try:
            file_extension = str(file_path).split(".")[-1]
            writer = self.get_action(file_extension, "write")
            writer(file_path, content)
        except Exception as e:
            print(f"Failed to write file {file_path}: {e}")

    def get_action(self, file_extension, action_type):
        """Gets the appropriate action for a given file extension and action type."""
        file_actions = self.file_actions.get(file_extension)
        if not file_actions:
            raise ValueError(f"Unsupported file type: {file_extension}")

        action = file_actions.get(action_type)
        if not action:
            raise ValueError(f"Unsupported action type: {action_type}")

        return action

    @staticmethod
    def read_markdown(file_path):
        """Reads the content of a Markdown file."""
        with open(file_path, encoding="utf-8") as file:
            return file.read()

    @staticmethod
    def read_toml(file_path):
        """Reads the content of a TOML file."""
        with open(file_path, encoding="utf-8") as file:
            data = toml.load(file)
        data_cleaned = {key.lower(): value for key, value in data.items()}
        return data_cleaned

    @staticmethod
    def read_json(file_path):
        """Reads the content of a JSON file."""
        with open(file_path, encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def write_markdown(file_path, content):
        """Writes the content to a Markdown file."""
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    @staticmethod
    def write_toml(file_path, content):
        """Writes the content to a TOML file."""
        with open(file_path, "w", encoding="utf-8") as file:
            toml.dump(content, file)

    @staticmethod
    def write_json(file_path, content):
        """Writes the content to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(content, file, ensure_ascii=False, indent=4)
