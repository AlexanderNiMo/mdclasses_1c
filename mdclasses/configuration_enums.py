import enum


class Format(enum.Enum):

    EDT = 'edt'
    CONFIGURATOR = 'configurator'


class ObjectType(enum.Enum):
    UNDEFINED = ''
    CONFIGURATION = 'Configuration'
    INFORMATION_REGISTER = "InformationRegister"
    FUNCTIONAL_OPTION = "FunctionalOption"
    STYLE_ITEM = "StyleItem"
    CONSTANT = "Constant"
    COMMON_MODULE = "CommonModule"
    DEFINED_TYPE = "DefinedType"
    CHART_OF_CHARACTERISTIC_TYPES = "ChartOfCharacteristicTypes"
    SCHEDULED_JOB = "ScheduledJob"
    XDTO_PACKAGE = "XDTOPackage"
    LANGUAGE = "Language"
    COMMON_TEMPLATE = "CommonTemplate"
    COMMAND_GROUP = "CommandGroup"
    REPORT = "Report"
    ROLE = "Role"
    WEBSERVICE = "WebService"
    CATALOG = "Catalog"
    SESSION_PARAMETER = "SessionParameter"
    INTERFACE = "Interface"
    DOCUMENT = "Document"
    DOCUMENT_JOURNAL = "DocumentJournal"
    EXCHANGE_PLAN = "ExchangePlan"
    DATA_PROCESSOR = "DataProcessor"
    COMMON_COMMAND = "CommonCommand"
    COMMON_PICTURE = "CommonPicture"
    STYLE = "Style"
    FILTER_CRITERION = "FilterCriterion"
    SUBSYSTEM = "Subsystem"
    FUNCTIONAL_OPTIONS_PARAMETER = "FunctionalOptionsParameter"
    ENUM = "Enum"
    COMMON_FORM = "CommonForm"
    SETTINGS_STORAGE = "SettingsStorage"
    EVENT_SUBSCRIPTION = "EventSubscription"
    COMMON_ATTRIBUTE = 'CommonAttribute'
    HTTP_SERVICE = 'HTTPService'
    WS_REFERENCE = 'WSReference'
    DOCUMENT_NUMERATOR = 'DocumentNumerator'
    SEQUENCE = 'Sequence'
    ACCUMULATION_REGISTER = 'AccumulationRegister'
    CHART_OF_ACCOUNTS = 'ChartOfAccounts'
    ACCOUNTING_REGISTER = 'AccountingRegister'
    BUSINESS_PROCESS = 'BusinessProcess'
    TASK = 'Task'
    CHART_OF_CALCULATION_TYPES = 'ChartOfCalculationTypes'
    CALCULATION_REGISTER = 'CalculationRegister'
    EXTERNAL_DATA_SOURCE = 'ExternalDataSource'
    DIMENSION_TABLE = 'DimensionTable'
    RECALCULATION = 'Recalculation'
    FORM = 'Form'
    TEMPLATE = 'Template'
    MODULE = 'Module'
    COMMAND = 'Command'
    TABLE = 'Table'
    CUBE = 'Cube'


class SupportType(enum.Enum):
    NOT_EDITABLE = 0
    EDITABLE_SUPPORT_ENABLED = 1
    NOT_SUPPORTED = 2
    NONE_SUPPORT = 3