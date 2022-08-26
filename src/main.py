from ortools.linear_solver import pywraplp
from PIL import Image
import numpy as np


def process_image(file):
    img = Image.open(file)

    # convert the image to black and white
    img = img.convert("1")

    # scale the image and make sure the size is divisible by 2
    scale = 0.1
    width, height = img.size
    size = ((int(width * scale) // 2) * 2, (int(height * scale) // 2) * 2)
    print("INFO: Height is {} and width is {}".format(size[1], size[0]))
    img = img.resize(size)

    # show the image
    img.show()

    # convert to a 2d array of booleans
    grid = np.array(img)
    return grid


def solver_init(grid, height, width):
    solver = pywraplp.Solver("binart solver", pywraplp.Solver.SAT_INTEGER_PROGRAMMING)
    if not solver: return

    # create a dictionary with all the integer variables (use as intvars[x, y])
    positions = [(x, y) for y in range(height) for x in range(width)]
    intvars = {(x, y): solver.IntVar(0, 1, "x{};y{}".format(x, y)) for x, y in positions}
    print("INFO: Number of variables is", solver.NumVariables())

    return solver, intvars


def constraint_consecutive(solver, intvars, height, width):
    # no more than 2 consecutive 0's or 1's per row
    for y in range(height):
        for x in range(width - 2):
            solver.Add(1 <= intvars[x, y] + intvars[x + 1, y] + intvars[x + 2, y])
            solver.Add(2 >= intvars[x, y] + intvars[x + 1, y] + intvars[x + 2, y])

    # no more than 2 consecutive 0's or 1's per column
    for x in range(width):
        for y in range(height - 2):
            solver.Add(1 <= intvars[x, y] + intvars[x, y + 1] + intvars[x, y + 2])
            solver.Add(2 >= intvars[x, y] + intvars[x, y + 1] + intvars[x, y + 2])


def constraint_balance(solver, intvars, height, width):
    # same number of 0's and 1's in every row
    for y in range(height):
        solver.Add(sum(intvars[x, y] for x in range(width)) == width // 2)

    # same number of 0's and 1's in every column
    for x in range(width):
        solver.Add(sum(intvars[x, y] for y in range(height)) == height // 2)


def constraint_uniqueness(solver, intvars, height, width):
    pass # TODO


def solver_constraint(solver, intvars, height, width):
    # add the constraints of a binairo puzzle
    constraint_consecutive(solver, intvars, height, width)
    constraint_balance(solver, intvars, height, width)
    constraint_uniqueness(solver, intvars, height, width)

    print('INFO: Number of constraints =', solver.NumConstraints())


def solver_goal(solver, intvars, grid):
    # maximize the similarity of the image and the puzzle
    goal = solver.IntVar(0, 0, "placeholder goal")

    for y in range(len(grid)):
        for x in range(len(grid[0])):
            if grid[y][x]:
                goal += intvars[x, y]
            else:
                goal += 1 - intvars[x, y]

    solver.Maximize(goal)


def solver_solve(solver, height, width):
    # solve the problem automatically
    status = solver.Solve()

    print('INFO: Problem solved in %d iterations' % solver.iterations())
    print('INFO: Problem solved in %f milliseconds' % solver.wall_time())

    if status == pywraplp.Solver.OPTIMAL:
        print('INFO: Optimal solution found')
        print("INFO: Maximized score =", solver.Objective().Value())
        score = solver.Objective().Value() / (height * width / 2)
        print("INFO: Relative score = {:.2f}".format(score))
        return True
    else:
        print('INFO: No optimal solution found')
        return False


def solver_image(solver, intvars, height, width):
    # create a new image of the solved puzzle
    newgrid = [[intvars[x, y].solution_value() for x in range(width)] for y in range(height)]
    newgrid = np.vectorize(lambda v: 0 if v == 0 else 255)(newgrid)

    newgrid = np.asarray(dtype=np.dtype('uint8'), a=newgrid)
    img = Image.frombytes(mode='1', size=newgrid.shape[::-1], data=np.packbits(newgrid, axis=1))

    # show the new image
    img.show()
    img.save("puzzle.png")


def main():
    grid = process_image("res/example2.jpg")
    height, width = len(grid), len(grid[0])
    solver, intvars = solver_init(grid, height, width)

    solver_constraint(solver, intvars, height, width)
    solver_goal(solver, intvars, grid)

    if not solver_solve(solver, height, width): return
    solver_image(solver, intvars, height, width)


if __name__ == "__main__":
    main()
