from pydantic import BaseModel, Field, validator
from typing import Literal
from fastapi import HTTPException, status
from acc_prov import STATES_DATA_TYPE, get_cities, get_states


