from typing import List


class Form:

    def __init__(self):

        self.attributes: List[FormAttribute] = list()
        self.elements: List[FormElement] = list()

        self.options: List[FormOption] = list()
        self.commands: List[FormCommand] = list()


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