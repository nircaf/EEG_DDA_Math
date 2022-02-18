import random
import sys


def random_math_problem():
    operators = ['+', '-', '*', '/']
    n1 = round(random.uniform(0.1, 10), 2)
    n2 = round(random.uniform(0.1, 10), 1)
    operator = random.choice(operators)
    if operator == "+":
        ans = n1 + n2
    elif operator == "-":
        ans = n1 - n2
    elif operator == "*":
        ans = n1 * n2
    elif operator == "/":
        ans = n1 / n2
    print
    "What is {} {} {}?\n".format(n1, operator, n2)
    return ans


def ask_question():
    ans = random_math_problem()
    response = input()
    return response, ans


def mathquiz():
    print
    "This is a math quiz to practice arithmetic. Input 'q' at any prompt to exit the program. Ready to take the math test? (y/n)\n"
    x = input()
    while x not in ['y', 'n', 'q']:
        print
        "Invalid input. Please try again with either y/n/q."
        x = input()
    if x == 'n':
        print
        "Okay, exiting the math quiz. Goodbye."
        sys.exit()
    elif x == 'y':
        print
        "Okay, let's begin the quiz.\n"
    elif x == 'q':
        print
        "Okay, exiting the math quiz. Goodbye."
        sys.exit()

    score = 0
    questions = 0
    while (True):
        inputs = ask_question()
        response = inputs[0]
        ans = inputs[1]
        if response == 'q':
            print
            "Okay, exiting the math quiz. Goodbye."
            sys.exit()
        elif response == ans:
            score += 1
            questions += 1
            print
            "Correct!\n" + "Current score = {}".format(score) + "/{}".format(questions)
        else:
            questions += 1
            print
            "Incorrect :(\n" + "Correct Answer = {}\n".format(ans) + "Current score = {}".format(score) + "/{}".format(
                questions)
    return "Your score was {}/{}".format(score, questions)


mathquiz()