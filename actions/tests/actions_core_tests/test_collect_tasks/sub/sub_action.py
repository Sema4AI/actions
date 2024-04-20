from sema4ai.actions import action


def some_sub_method():
    print("In some sub method")


@action
def sub():
    some_sub_method()
