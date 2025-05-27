# Module `create_executable`

*Fichier source : `create_executable.py`*

## Fonctions
- [`create_executable()`](#create_executable)

---

## `create_executable()` { #create_executable }

```python
def create_executable()
```

Create an executable for the sensor system application
This function generates a PyInstaller executable package for the sensor system.
It creates a spec file, copies necessary data files, and packages everything 
into a standalone executable that can run without Python installed.
Returns:
bool: True if the executable was created successfully, False otherwise

---

