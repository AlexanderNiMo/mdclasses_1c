from typing import List, Optional
from pathlib import Path

from mdclasses.Module import create_module, ModuleParser, Module


class Form:

    def __init__(self, description_path: Path, structure_path: Path):

        self.attributes: List[FormAttribute] = list()
        self.elements: List[FormElement] = list()

        self.options: List[FormOption] = list()
        self.commands: List[FormCommand] = list()

        self.module: Optional[Module] = None

        self.description_path = description_path
        self.structure_path = structure_path

        self.name = description_path.stem

        self._read_module()

    def _read_module(self):
        ext_path = self.description_path.parent.joinpath(self.description_path.stem, 'Ext', 'Form')

        if not ext_path.exists():
            return

        parser = ModuleParser()

        for element in ext_path.iterdir():
            if element.is_file() and element.suffix == '.bsl':
                self.module = create_module(parser, element)

    def read_structure(self):
        pass


class FormOption:

    def __init__(self):
        pass


class FormAttribute:

    def __init__(self):
        pass


class FormCommand:

    def __init__(self):
        pass


class FormElement:

    def __init__(self):
        pass