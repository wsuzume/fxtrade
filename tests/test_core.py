from fxtrade.core import is_instance_list

def test_is_instance_list():
    xs = ['aa', 'bb', 'cc']

    assert is_instance_list(xs, str)
    assert is_instance_list(xs, str, n=3)

    assert not is_instance_list(3, str)
    assert not is_instance_list({'a': 'b'}, str)
    assert not is_instance_list(xs, str, n=2)