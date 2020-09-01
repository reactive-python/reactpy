def assert_unordered_equal(x, y):
    list_x = list(x)
    list_y = list(y)

    assert len(x) == len(y) and all(
        # this is not very efficient unfortunately so don't compare anything large
        list_x.count(value) == list_y.count(value)
        for value in list_x
    )
