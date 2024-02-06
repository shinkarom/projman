class Tokenizer:
    def __init__(self, s):
        self.string = s
        self.pos = 0
        self.l = len(self.string)
    def current(self):
        return self.string[self.pos]
    def get_token(self):
        s = ""
        while self.pos < self.l and self.current().isspace():
            self.pos += 1
        while self.pos < self.l and not self.current().isspace():
            s += self.current()
            self.pos += 1
        return s
    def get_string(self):
        s = ""
        while self.pos < self.l and self.current().isspace():
            self.pos += 1
        while self.pos < self.l:
            s += self.current()
            self.pos += 1
        s = s.strip()
        return s
    def require_int(self):
        s = self.get_token()
        if s.isnumeric():
            return s
        else:
            print("Error: integer required, but got", s)
            return None
    def require_word(self):
        s = self.get_token()
        if not s.isnumeric():
            return s
        else:
            print("Error: word required, but got", s)
            return None
    def require_specific_word(self, t):
        s = self.require_word()
        if s != None:
            if s.lower() == t.lower():
                return s
            else:
                print(f"Error: required {t}, but got {s}")
                return None