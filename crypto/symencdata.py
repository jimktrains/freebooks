import base64
class SymEncData:
    def __init__(self, algo, mode, bs, iv, data):
        self.algo = algo
        self.mode = mode
        self.bs = bs
        self.iv = iv
        self.data = data

    def __str__(self):
        return repr(self)
    def __repr__(self):
        return "%s:%s:%s:%s:%s" % (self.algo, self.mode, self.bs, 
                                   base64.b64encode(self.iv), 
                                   base64.b64encode(self.data))
    def to_dict(self):
        return {
            'algo': self.algo,
            'mode': self.mode,
            'block_size': self.bs,
            'iv':  base64.b64encode(self.iv),
            'data': base64.b64encode(self.data)
        }

    @staticmethod
    def from_dict(state):
        return SymEncData(state['algo'], state['mode'], state['block_size'],
                          base64.b64decode(state['iv']),
                          base64.b64decode(state['data']))
