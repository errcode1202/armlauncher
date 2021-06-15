class Confluence:

    def __new__(cls, p, u, r, k):
        return object.__new__(cls)

    def __init__(self, p, u, r, k):
        self.product = p
        self.url = u
        self.region = r
        self.key = k
        self.parameters()

    def parameters(self):
        parameters = {
            'ConfClusterSize': "trial",
            '_artifactsLocation': self.url,
            'sshKey': self.key,
            'sshUserName': f"{self.product}admin",
            'location': self.region,
            'dbPassword': ".Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69",
            'confAdminUserName': "confadmin",
            'confAdminUserPassword': ".Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69",
            'enableAnalytics': False
        }

        return {k: {'value': v} for k, v in parameters.items()}
