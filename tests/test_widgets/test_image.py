import idom


def test_image_from_string(driver, driver_wait, display):
    src = """
    <svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="100" style="fill:rgb(0,0,255);" />
    </svg>
    """
    img = idom.Image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert img.base64_source in client_img.get_attribute("src")

    img2 = idom.Image("svg", attributes={"id": "a-circle-2"})
    img2.io.write(src)
    display(img2)
    client_img = driver.find_element_by_id("a-circle-2")
    assert img.base64_source in client_img.get_attribute("src")


def test_image_from_bytes(driver, driver_wait, display):
    src = b"""
    <svg width="400" height="110" xmlns="http://www.w3.org/2000/svg">
      <rect width="300" height="100" style="fill:rgb(0,0,255);" />
    </svg>
    """
    img = idom.Image("svg", src, {"id": "a-circle-1"})
    display(img)
    client_img = driver.find_element_by_id("a-circle-1")
    assert img.base64_source in client_img.get_attribute("src")

    img2 = idom.Image("svg", attributes={"id": "a-circle-2"})
    img2.io.write(src)
    display(img2)
    client_img = driver.find_element_by_id("a-circle-2")
    assert img.base64_source in client_img.get_attribute("src")
