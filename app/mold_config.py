"""
mold_config.py defines classes and methods for creating thermocouple array on application initialization
"""
from thermocouple import Thermocouple
from pyCommonlySharedCode.MouldDimensions import get_mould_dimensions
from pyCommonlySharedCode.generalFunctions import get_plantdatadir_and_plantconfig


class MouldSide:
    """
    This class stores lists of X, Y and Z coordinates and labels of thermocouples on the mould side.
    Each mould side also stores its name.
    """
    def __init__(self, name, x, y, z, labels) -> None:
        super().__init__()
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.labels = labels
        self.text_labels = [f'TC {num}' for num in self.labels]

    def to_dict(self):
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'labels': self.labels,
        }


class MouldConfig:
    """
    This class stores necessary information about the mould retrieved from the config file
    """
    def __init__(self, mold_no, name, tc_count, mold_sides) -> None:
        super().__init__()
        self.name = name
        self.tc_count = tc_count
        self.mold_sides = mold_sides
        self.mold_no = mold_no

    @classmethod
    def from_common_config(cls):
        """
        This method uses pyCommonlySharedCode submodule for reading mould info.

        :return: an instance of MouldConfig class
        """
        def get_list(ndarr):
            return list(map(int, ndarr.flatten().tolist()))

        def get_mould_sides(mould_dims):
            mould_sides = []
            for mold_side_name in mould_dims.ActSideStr:
                mold_side_info = mould_dims.get_mould_side_dimensions(mold_side_name)
                mesh = mold_side_info.Mesh
                x_list = get_list(mesh.X)
                y_list = get_list(mesh.Y)
                z_list = get_list(mesh.Z)
                labels = get_list(mesh.ID)
                mold_side = MouldSide(mold_side_name, x_list, y_list, z_list, labels)
                mould_sides.append(mold_side)
            return mould_sides

        mould_dims = get_mould_dimensions(*get_plantdatadir_and_plantconfig())
        tc_count = mould_dims.Mould.TotalSensorCnt
        mould_sides = get_mould_sides(mould_dims)
        mold_no = str(int(mould_dims.Mould.ID))
        mould_name = f"{mold_no}_{mould_dims.Mould.Label}"
        return cls(mold_no, mould_name, tc_count, mould_sides)


def tcs_from_config(mold_config):
    """
    Method for generating initial thermocouple array.

    :param mold_config: MouldConfig instance
    :return: list of instances of Thermocouple class
    """
    tcs = {}
    for side in mold_config.mold_sides:
        mold_side_tcs = {
            label: Thermocouple(x, y, label, side.name)
            for x, y, label in list(zip(side.x, side.y, side.labels))
        }
        tcs.update(mold_side_tcs)
    return tcs
