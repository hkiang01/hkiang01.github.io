---
title: "Testing Abstractions"
weight: 1
draft: false
---

- [TL;DR](#tldr)
- [Setting the stage](#setting-the-stage)
- [The Library](#the-library)
- [Natural Evolution of (Bad) Tests](#natural-evolution-of-bad-tests)
- [Better ([DRY]) tests](#better-dry-tests)

### TL;DR
[Parametrizing fixtures] can enable testing all derived classes of a given base class while keeping tests [DRY].

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

### The Library

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

### Natural Evolution of (Bad) Tests

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

<!-- ![puke](https://media3.giphy.com/media/dOl2LFw0RbTMc/giphy.gif?cid=ecf05e471cok6ox2v6bc6odlnxriokonvouq2lqb38h9iua4&rid=giphy.gif&ct=g) -->

Stop it.

### Better ([DRY]) tests

[Parametrizing fixtures]: https://docs.pytest.org/en/latest/how-to/fixtures.html#fixture-parametrize
[Write once, run anywhere]: https://en.wikipedia.org/wiki/Write_once,_run_anywhere
[DRY]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
