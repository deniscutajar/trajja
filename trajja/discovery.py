from miio.cloud import CloudInterface


def get_mi_devices(username):
    """
    Return the Mi Devices connected with username and password
    :param username: Mi Cloud username
    :return:
    """
    password = input("Please enter your Mi account password: ")
    ci = CloudInterface(username=username, password=password)
    devs = ci.get_devices()
    for did, dev in devs.items():
        print(f"[{dev.description}] {dev.ssid} {dev.name} {dev.ip} {dev.token}")

    return devs
