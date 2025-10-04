from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from python import statesurf


class SimulateCommandTest(unittest.TestCase):
    def test_simulate_generates_assets(self) -> None:
        with TemporaryDirectory() as tmp:
            sim_dir = Path(tmp) / "sim"
            statesurf.simulate(
                input_path=Path("plantuml/hsm.puml"),
                simulation_dir=sim_dir,
                machine_name="TestMachine",
                plantuml_cmd="plantuml",
            )

            machine_file = sim_dir / "machine.py"
            simulator_file = sim_dir / "simulator.py"
            model_copy = sim_dir / "hsm.puml"

            self.assertTrue(machine_file.exists(), "machine.py should be generated")
            self.assertTrue(simulator_file.exists(), "simulator.py should be generated")
            self.assertTrue(model_copy.exists(), "A copy of the original PlantUML file should be present")

            machine_content = machine_file.read_text(encoding="utf-8")
            self.assertIn("class HsmMachine", machine_content)

            simulator_content = simulator_file.read_text(encoding="utf-8")
            self.assertIn("nicegui", simulator_content.lower())


if __name__ == "__main__":
    unittest.main()
