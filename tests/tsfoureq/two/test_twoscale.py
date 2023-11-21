# SPDX-FileCopyrightText: 2020-2023 JosiePy Development Team
#
# SPDX-License-Identifier: BSD-3-Clause

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np


from josie.bc import Dirichlet, Direction, make_periodic
from josie.boundary import Line
from josie.mesh import Mesh
from josie.mesh.cell import SimpleCell, MUSCLCell
from josie.mesh.cellset import MeshCellSet
from josie.tsfoureq.solver import TSFourEqSolver
from josie.general.schemes.space.muscl import MUSCL
from josie.tsfoureq.state import Q
from josie.tsfoureq.eos import TwoPhaseEOS, LinearizedGas


from josie.twofluid.fields import Phases


def relative_error(a, b):
    return np.abs(a - b)


def riemann2Q(state, eos):
    """Wrap all the operations to create a complete TSFourEq state from the
    initial Riemann Problem data
    """
    # BC
    arho1 = state.alphabar * state.rho1 * (1 - state.ad)
    arho2 = (1.0 - state.alphabar) * state.rho2 * (1 - state.ad)
    arho1d = eos[Phases.PHASE1].rho0 * state.ad
    rho = arho1 + arho2 + arho1d
    arho = state.alphabar * rho
    rhoU = rho * state.U
    rhoV = 0.0
    V = 0.0
    p1 = eos[Phases.PHASE1].p(state.rho1)
    p2 = eos[Phases.PHASE2].p(state.rho2)
    c1 = eos[Phases.PHASE1].sound_velocity(state.rho1)
    c2 = eos[Phases.PHASE2].sound_velocity(state.rho2)
    P = state.alphabar * p1 + (1.0 - state.alphabar) * p2
    c = np.sqrt((arho1 * c1**2 + arho2 * c2**2) / rho) / (1 - state.ad)

    return Q(
        arho,
        rhoU,
        rhoV,
        rho,
        state.U,
        V,
        P,
        c,
        state.alphabar,
        arho1,
        p1,
        c1,
        arho2,
        p2,
        c2,
        arho1d,
        state.ad,
    )


def test_twoscale(riemann_state, Scheme, write, request):
    left = Line([0, 0], [0, 1])
    bottom = Line([0, 0], [2, 0])
    right = Line([2, 0], [2, 1])
    top = Line([0, 1], [2, 1])

    eos = TwoPhaseEOS(
        phase1=LinearizedGas(p0=1e5, rho0=1.0, c0=3.0),
        phase2=LinearizedGas(p0=1e5, rho0=1e3, c0=15.0),
    )

    Q_left = riemann2Q(riemann_state.left, eos)
    Q_right = riemann2Q(riemann_state.right, eos)
    Q_small_scale = riemann2Q(riemann_state.small_scale, eos)

    left.bc = Dirichlet(Q_left)
    right.bc = Dirichlet(Q_right)
    bottom, top = make_periodic(bottom, top, Direction.Y)

    if issubclass(Scheme, MUSCL):
        mesh = Mesh(left, bottom, right, top, MUSCLCell)
    else:
        mesh = Mesh(left, bottom, right, top, SimpleCell)
    mesh.interpolate(128, 64)
    mesh.generate()

    def init_fun(cells: MeshCellSet):
        xc = cells.centroids[..., 0]
        yc = cells.centroids[..., 1]
        x0 = 1
        y0 = 0.5
        # R = 0.1

        idx_left = np.where(xc <= riemann_state.xd)
        idx_right = np.where(xc > riemann_state.xd)
        # Circle
        # idx_small_scale = np.where((xc - x0) ** 2 + (yc - y0) ** 2 < R ** 2)
        # central beam
        idx_small_scale = np.where((np.abs(yc - y0) < 0.1) * (np.abs(xc - x0) < 0.5))

        cells.values[idx_left[0], idx_left[1], :] = Q_left
        cells.values[idx_right[0], idx_right[1], :] = Q_right
        cells.values[idx_small_scale[0], idx_small_scale[1], :] = Q_small_scale

    scheme = Scheme(eos, do_relaxation=True)
    solver = TSFourEqSolver(mesh, scheme)
    solver.init(init_fun)

    final_time = riemann_state.final_time
    t = 0.0
    CFL = riemann_state.CFL

    cells = solver.mesh.cells
    dt = scheme.CFL(cells, CFL)

    if write:
        import logging
        from datetime import datetime
        from josie.io.write.writer import XDMFWriter
        from josie.io.write.strategy import TimeStrategy

        logger = logging.getLogger("josie")
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(
            "two_scale_four_eq_Rusanov_Godunov.log"
        )
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)

        # Write strategy
        dt_save = final_time / 100
        strategy = TimeStrategy(dt_save=dt_save, animate=False)
        writer = XDMFWriter(
            "two_scale_four_eq_Rusanov_Godunov.xdmf",
            strategy,
            solver,
            final_time=final_time,
            CFL=CFL,
        )

        writer.solve()
    else:
        while t <= final_time:
            dt = scheme.CFL(cells, CFL)

            assert ~np.isnan(dt)

            solver.step(dt)

            t += dt
            print(f"Time: {t}, dt: {dt}")

        # Check that we reached the final time
        assert t >= final_time
