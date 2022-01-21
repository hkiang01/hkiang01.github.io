import pytest


class Base:
    def do_the_thing(self) -> str:
        raise NotImplementedError

    def do_the_other_thing(self) -> str:
        raise NotImplementedError

    def do_this_thing(self) -> str:
        raise NotImplementedError

    def do_that_thing(self) -> str:
        raise NotImplementedError


class DerivedA(Base):
    def do_the_thing(self) -> str:
        return "I did it"

    def do_the_other_thing(self) -> str:
        return "I did it"

    def do_this_thing(self) -> str:
        return "I did it"

    def do_that_thing(self) -> str:
        return "I did it"


class DerivedB(Base):
    def do_the_thing(self) -> str:
        return "I did it better"

    def do_the_other_thing(self) -> str:
        return "I did it better"

    def do_this_thing(self) -> str:
        return "I did it better"

    def do_that_thing(self) -> str:
        return "I did it better"


@pytest.fixture(params=[cls for cls in Base.__subclasses__()])
def base(request) -> Base:
    if request.param == DerivedA:
        return DerivedA()
    elif request.param == DerivedB:
        return DerivedB()


def test_do_the_thing(base: Base):
    result = base.do_the_thing()
    assert "I did it" in result


def test_do_the_other_thing(base: Base):
    result = base.do_the_other_thing()
    assert "I did it" in result


def test_do_this_thing(base: Base):
    result = base.do_this_thing()
    assert "I did it" in result


def test_do_that_thing(base: Base):
    result = base.do_that_thing()
    assert "I did it" in result
