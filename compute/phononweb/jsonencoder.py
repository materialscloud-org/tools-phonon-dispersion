# Copyright (c) 2017, Henrique Miranda
# All rights reserved.
#
# This file is part of the phononwebsite project
#
""" Code the dictionary in json format """
import json
import numpy as np


class JsonEncoder(json.JSONEncoder):
    """Custom JSON encoder working correctly also with numpy arrays."""

    def default(self, obj):  # pylint: disable=method-hidden, arguments-differ
        """Default encoder."""
        if isinstance(obj, (np.ndarray, np.number)):
            if np.iscomplexobj(obj):
                return [obj.real, obj.imag]
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
