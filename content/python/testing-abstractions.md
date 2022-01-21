---
title: "Testing Abstractions"
weight: 1
draft: false
---

- [TL;DR](#tldr)
- [Setting the stage](#setting-the-stage)
- [Natural Evolution of (Bad) Tests](#natural-evolution-of-bad-tests)
- [The secret sauce](#the-secret-sauce)
- [Full example](#full-example)
- [What does this mean?](#what-does-this-mean)

### TL;DR
[Parametrizing fixtures] can enable testing all derived classes of a given base class while keeping tests [DRY].
Check out [The secret sauce](#the-secret-sauce).

### Setting the stage
You'll eventually get to a point where you decide to start maintaining a Python package to include all of your standard logic used in multiple projects.
This has a few advantages:

- Take advantage of existing package management solutions for a smooth upgrade process
  - poetry, pip, etc.
- Reuse: "[Write once, run anywhere]"
  - Easy to sell to your boss, other money people
  - Applies to both implementation and tests
- Take advantage of [inheritance](https://docs.python.org/3/tutorial/classes.html#inheritance)
  - i.e., `class Base` can be implemented by `class DerivedA`, and `class DerivedB`

The last bit is quite valuable: Let's say there's a vendor offering that your company's applications use via the `class Base` abstractoin in your Python package.
Said vendor offering can be implemented directly in `class DerivedA`.
However, it's been determined that a separate vendor offering will be a better fit going forward.

The switch from the "old" vendor offering to the "new" would then look something like this:
- implement the "new" vendor offering in `class DerivedB` in a new version of the Python package
- update the package in the application
- change the application logic to use the `class DerivedB` to ultimately use the "new" vendor offering behind-the-scenes

Great, but what about tests?
The promise of "[Write once, run anywhere]" isn't as obvious.
Luckily, we can take advantage of [Parametrizing fixtures] so as to keep our tests [DRY].
Now let's see a more concrete example

### Natural Evolution of (Bad) Tests

Let's say our library code looks like this
```python
# library/module.py
class Base:
  def do_the_thing(self) -> str:
    raise NotImplementedError

class DerivedA(Base):
  def do_the_thing(self) -> str:
    return "I did it"

class DerivedB(Base):
  def do_the_thing(self) -> str:
    return "I did it better"
```

This is what our tests would look like if we just had them written for `DerivedA`:

```python
import pytest

def test_do_the_thing():
  base: Base = DerivedA()
  result = base.do_the_thing()
  assert "I did it" in result
```

Okay, then naturally we'll just add another test for `DerivedB` such that our tests look like this:

```python
def test_do_the_thing_a():
  base: Base = DerivedA()
  result = base.do_the_thing()
  assert "I did it" in result

def test_do_the_thing_b():
  base: Base = DerivedB()
  result = base.do_the_thing()
  assert "I did it" in result
```

It's easy to see how this can be a bit repetitive, especially if the base class looks like this:

```python
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
```

Then your tests would look like this:

```python
def test_do_the_thing_a():
  base: Base = DerivedA()
  result = base.do_the_thing()
  assert "I did it" in result

def test_do_the_thing_b():
  base: Base = DerivedB()
  result = base.do_the_thing()
  assert "I did it" in result

def test_do_the_other_thing_a():
  base: Base = DerivedA()
  result = base.do_the_other_thing()
  assert "I did it" in result

def test_do_the_other_thing_b():
  base: Base = DerivedB()
  result = base.do_the_other_thing()
  assert "I did it" in result

def test_do_this_thing_a():
  base: Base = DerivedA()
  result = base.do_this_thing()
  assert "I did it" in result

def test_do_this_thing_b():
  base: Base = DerivedB()
  result = base.do_this_thing()
  assert "I did it" in result

def test_do_that_thing_a():
  base: Base = DerivedA()
  result = base.do_that_thing()
  assert "I did it" in result

def test_do_that_thing_b():
  base: Base = DerivedB()
  result = base.do_that_thing()
  assert "I did it" in result
```

This is what you're doing when writing stuff like above.

![puke](https://media3.giphy.com/media/dOl2LFw0RbTMc/giphy.gif?cid=ecf05e471cok6ox2v6bc6odlnxriokonvouq2lqb38h9iua4&rid=giphy.gif&ct=g)

Stop it.
You know you can do better.
So do better.

### The secret sauce
![sauce](https://media2.giphy.com/media/vRZWXn6DpqvoB7UdR2/giphy.gif?cid=ecf05e47ksvj8udiv9yggxpcyk0vvxmbl1bw9mh5inyvqssq&rid=giphy.gif&ct=g)


Instead, your tests can look like this:

```python
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
```

[Parametrizing fixtures] is what makes the above possible:

```python
@pytest.fixture(params=[cls for cls in Base.__subclasses__()])
def base(request) -> Base:
  if request.param == DerivedA:
    return DerivedA()
  elif request.param == DerivedB:
    return DerivedB()
```

What is happening, exactly?
The docs can say it best:
> The main change is the declaration of params with @pytest.fixture, a list of values for each of which the fixture function will execute and can access a value via request.param. No test function code needs to change. 

### Full example

```python
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
```

### What does this mean?
If we implement `class Base` in a `class DerivedC`, we'll get the tests for free!

Note that `params=[cls for cls in Base.__subclasses__()]` makes this possible in the `base()` fixture.

This is pretty based lol


[Parametrizing fixtures]: https://docs.pytest.org/en/latest/how-to/fixtures.html#fixture-parametrize
[Write once, run anywhere]: https://en.wikipedia.org/wiki/Write_once,_run_anywhere
[DRY]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
