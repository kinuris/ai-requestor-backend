class PlainTextTranslator:
    def __init__(self, name, data, fields='*'):
        self.name = name

        if fields == '*':
            self.data = data
        elif isinstance(fields, list):
            self.data = []

            for data in data:
                relevant = {
                    field: data[field] for field in fields
                }

                self.data.append(relevant)
        else:
            raise ValueError("'fields' parameter must be '*' or a list")
            
    def translate(self):
        result = f"{self.name}:\n"

        for data in self.data:
            accum = "- "

            for key, value in data.items():
                accum += f"{key}: {value}"
                if key != list(data.keys())[-1]:
                    accum += ", "

            result += accum + "\n"

        return result
            