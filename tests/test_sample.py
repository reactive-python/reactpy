from idom.sample import run_sample_app
from idom.server.utils import find_available_port


def test_sample_app(driver):
    host = "127.0.0.1"
    port = find_available_port(host, allow_reuse_waiting_ports=False)

    run_sample_app(host=host, port=port, run_in_thread=True)

    driver.get(f"http://{host}:{port}")

    h1 = driver.find_element("tag name", "h1")

    assert h1.get_attribute("innerHTML") == "Sample Application"
