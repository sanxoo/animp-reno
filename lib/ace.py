
def get_host_by_port(port):
    return "localhost"

def get_addr_by_port(port):
    host = get_host_by_port(port)
    return (host, port)

