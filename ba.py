import json
if __name__ == '__main__':
   bla = "{'appEndpoint': {'type': 'String', 'value': 'http://jira-appgtwyip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'bastionUrl': {'type': 'String', 'value': 'jira-jumpboxip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'sshUrl': {'type': 'String', 'value': 'ssh jiraadmin@jira-jumpboxip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'jdbcUrl': {'type': 'String', 'value': 'jdbc:sqlserver://jirasqlserverzupehpxx4guka.database.windows.net:1433;database=jiradatabase;user=jira@jirasqlserverzupehpxx4guka;password=.Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69'}}"
   parsed = json.loads(bla)
   print(json.dumps(parsed, indent=4, sort_keys=True))




{'appEndpoint': {'type': 'String', 'value': 'http://jira-appgtwyip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'bastionUrl': {'type': 'String', 'value': 'jira-jumpboxip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'sshUrl': {'type': 'String', 'value': 'ssh jiraadmin@jira-jumpboxip-zupehpxx4guka.northeurope.cloudapp.azure.com'}, 'jdbcUrl': {'type': 'String', 'value': 'jdbc:sqlserver://jirasqlserverzupehpxx4guka.database.windows.net:1433;database=jiradatabase;user=jira@jirasqlserverzupehpxx4guka;password=.Jkv435jxaDKL2345KA7YpbLyWJLPmocWx43rcn69'}}