import base64
class ASymEncData:
    def __init__(self, curve, data):
        self.curve = curve
        self.data = data

    def __str__(self):
        return repr(self)
    def __repr__(self):
        return "%s:%s" % (self.curve, base64.b64encode(self.data))

    def to_dict(self):
        return {
            'curve': self.curve,
            'data': base64.b64encode(self.data)
        }

    @staticmethod
    def from_dict(state):
        return ASymEncData(state['curve'], state['data'])
