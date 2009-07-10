# This program is public domain
"""
Periodic table definition, with classes for elements and isotopes.

PeriodTable
    Creates an empty periodic table.  Properties are added to it
    separately.  Note this is not a singleton.  But unless you are
    very careful you should use the default table defined for the
    package.

Element
    A class to hold the properties for each element.

Isotope
    A class to hold the properties for individual isotopes.

Ion
    A class to hold the properties for individual ions.

Elements are accessed from a periodic table using table[number], table.name
or table.symbol where symbol is the two letter symbol.  Individual isotopes
are accessed using el[isotope].  Individual ions are references using
el.ion[charge].  If there are properties specific to the ion and the isotope,
they will be referenced by el[isotope].property[charge].

delayed_load(attrs, loader, element=True, isotope=False)
    Delay loading the element attributes until they are needed.

See the user manual for information on extending the periodic table
with your own attributes.
"""
__docformat__ = 'restructuredtext en'
__all__ = ['delayed_load', 'define_elements',
           'Ion', 'Isotope', 'Element', 'PeriodicTable']

import copy

def delayed_load(all_props,loader,element=True,isotope=False):
    """
    Delayed loading of an element property table.  When any of props
    is first accessed the loader will be called to load the associated
    data.  The help string starts out as the help string for the loader
    function.  If it is an isotope property, be sure to set the
    keyword isotope=True.
    """
    def clearprops():
        """
        Remove the properties so that the attribute can be accessed
        directly.
        """
        if element:
            for p in all_props:
                delattr(Element, p)
        if isotope:
            for p in all_props:
                delattr(Isotope, p)

    def getter(propname):
        """
        Property getter for attribute propname.

        The first time the prop is accessed, the prop itself will be
        deleted and the data loader for the property will be called
        to set the real values.  Subsequent references to the property
        will be to the actual data.
        """
        def getfn(el):
            #print "get",el,propname
            clearprops()
            loader()
            return getattr(el, propname)
        return getfn

    def setter(propname):
        """
        Property setter for attribute propname.

        This function is assumed to be called when the data loader for the
        attribute is called before the property is referenced (for example,
        if somebody imports periodictable.xsf before referencing Ni.xray). In
        this case, we simply need to clear the delayed load property and
        let the loader set the values as usual.

        If the user tries to override a value in the table before first
        referencing the table, then the above assumption is false.  E.g.,
        "Ni.K_alpha=5" followed by "print Cu.K_alpha" will yield an
        undefined Cu.K_alpha.  This will be difficult for future users
        to debug.
        """
        def setfn(el, value):
            #print "set",el,propname,value
            clearprops()
            setattr(el, propname, value)
        return setfn

    if element:
        for p in all_props:
            prop = property(getter(p), setter(p), doc=loader.__doc__)
            setattr(Element, p, prop)

    if isotope:
        for p in all_props:
            prop = property(getter(p), setter(p), doc=loader.__doc__)
            setattr(Isotope, p, prop)


# Define the element names from the element table.
class PeriodicTable(object):
    """
    Defines the period table of the elements with isotopes.

    Individidual elements are accessed by name, symbol or atomic number.
    Individual isotopes are addressable by element[mass_number] or
    elements.isotope('#-Xx').

    For example, the following all retrieve iron::

        elements[26]
        elements.Fe
        elements.symbol('Fe')
        elements.name('iron')
        elements.isotope('Fe')

    To get iron-56, use::

        elements[26][56]
        elements.Fe[56]
        elements.isotope('56-Fe')

    Deuterium and tritium are defined as D and T.  Some
    neutron properties are available in elements[0]

    To show all the elements in the table, use the iterator::

        for element in elements:  # lists the element symbols
            print el.symbol,el.number

    Properties can be added to the elements as needed, including mass, nuclear
    and X-ray scattering cross sections.  See the help(periodictable)
    for details.
    """
    def __init__(self):
        self.properties = []
        self._element = {}
        for Z,(name,symbol,ions) in element_base.iteritems():
            element = Element(name.lower(),symbol,Z,ions)
            self._element[element.number] = element
            setattr(self,symbol,element)

        # There are two specially named isotopes D and T
        self.D = self.H.add_isotope(2)
        self.D.name = 'deuterium'
        self.D.symbol = 'D'
        self.T = self.H.add_isotope(3)
        self.T.name = 'tritium'
        self.T.symbol = 'T'

    def __getitem__(self, Z):
        """
        Retrieve element Z
        """
        return self._element[Z]

    def __iter__(self):
        """
        Process the elements in Z order
        """
        Zlist = self._element.keys()
        Zlist.sort()
        for Z in Zlist:
            yield self._element[Z]

    def symbol(self, input):
        """
        Lookup the symbol in the periodic table (and make sure it is an element
        or deuterium or tritium (D or T).
        """
        if hasattr(self,input):
            value = getattr(self,input)
            if isinstance(value,(Element,Isotope)):
                return value
        raise ValueError("unknown element "+input)

    def name(self, input):
        """
        Lookup the full name of the element in the period table.
        """
        for el in self:
            if input == el.name: return el
        if input == self.D.name: return self.D
        if input == self.T.name: return self.T
        raise ValueError("unknown element "+input)

    def isotope(self, input):
        """
        Lookup the element or isotope in the periodic table. Elements
        are assumed to be given by the standard element symbols.  Isotopes
        are given by number-symbol, or D and T for 2-H and 3-H.
        """
        # Parse #-Sym or Sym
        # If # is not an integer, set isotope to -1 so that the isotope
        # lookup will fail later.
        parts = input.split('-')
        if len(parts) == 1:
            isotope = 0
            symbol = parts[0]
        elif len(parts) == 2:
            try:
                isotope = int(parts[0])
            except:
                isotope = -1
            symbol = parts[1]
        else:
            symbol = ''
            isotope = -1

        # All elements are attributes of the table
        # Check that the attribute is an Element or an Isotope (for D or T)
        # If it is an element, check that the isotope exists
        if hasattr(self,symbol):
            attr = getattr(self,symbol)
            if isinstance(attr,Element):
                # If no isotope, return the element
                if isotope == 0:
                    return attr
                # If isotope, check that it is valid
                if isotope in attr.isotopes:
                    return attr[isotope]
            elif isinstance(attr,Isotope):
                # D,T must not have an associated isotope; D[4] is meaningless.
                if isotope == 0:
                    return attr

        # If we can't parse the string as an element or isotope, raise an error
        raise ValueError("unknown element "+input)

    def list(self,*props,**kw):
        """
        list('prop1','prop2',...,format='format')
            Print a list of elements with the given set of properties.

        If format is given, then it must contain one %s for each property.
        """
        format = kw.pop('format',None)
        assert len(kw) == 0
        for el in self:
            try:
                L = tuple(getattr(el,p) for p in props)
            except AttributeError:
                # Skip elements which don't define all the attributes
                continue

            if format is None:
                print " ".join(str(p) for p in L)
            else:
                try:
                    print format%L
                except:
                    print "format",format,"args",L
                    raise

class IonSet(object):
    def __init__(self, element_or_isotope):
        self.element_or_isotope = element_or_isotope
        self.ionset = {}
    def __getitem__(self, charge):
        if charge not in self.ionset:
            if charge not in self.element_or_isotope.ions:
                raise ValueError("%(charge)d is not a valid charge for %(symbol)s"
                                 % dict(charge=charge,
                                        symbol=self.element_or_isotope.symbol))
            self.ionset[charge] = Ion(self.element_or_isotope, charge)
        return self.ionset[charge]

class Ion(object):
    """Periodic table entry for an individual ion.

    An ion is associated with an element.  In addition to the element
    properties (symbol, name, atomic number), it has specific ion
    properties (charge).  Properties not specific to the ion (i.e., charge)
    are retrieved from the associated element.
    """
    def __init__(self, element, charge):
        self.element = element
        self.charge = charge
    def __getattr__(self, attr):
        return getattr(self.element,attr)
    def __str__(self):
        el = str(self.element)
        if self.charge > 0:
            return el+'^{%d+}'%self.charge
        elif self.charge < 0:
            return el+'^{%d-}'%(-self.charge)
        else:
            return el
    def __repr__(self):
        return repr(self.element)+'.ion[%d]'%self.charge
    def __getstate__(self):
        """
        Can't pickle ions without breaking extensibility.
        Suppress it for now.
        """
        raise TypeError("cannot copy or pickle ions")

class Isotope(object):
    """Periodic table entry for an individual isotope.

    An isotope is associated with an element.  In addition to the element
    properties (symbol, name, atomic number), it has specific isotope
    properties (isotope number, nuclear spin, relative abundance).
    Properties not specific to the isotope (e.g., x-ray scattering factors)
    are retrieved from the associated element.
    """
    def __init__(self,element,isotope_number):
        self.element = element
        self.isotope = isotope_number
        self.ion = IonSet(self)
    def __getattr__(self,attr):
        return getattr(self.element,attr)
    def __str__(self):
        # Deuterium and Tritium are special
        if 'symbol' in self.__dict__:
            return self.symbol
        else:
            return "%d-%s"%(self.isotope,self.element.symbol)
    def __repr__(self):
        return "%s[%d]"%(self.element.symbol,self.isotope)
    def __getstate__(self):
        """
        Can't pickle isotopes without breaking extensibility.
        Suppress it for now.
        """
        raise TypeError("cannot copy or pickle isotopes")

class Element(object):
    """Periodic table entry for an element.

    An element is a name, symbol and number, plus a set of properties.
    Individual isotopes can be referenced as element[isotope_number].
    Individual ionization states can be referenced by element.ion[charge]
    """
    def __init__(self,name,symbol,Z,ions):
        self.name = name
        self.symbol = symbol
        self.number = Z
        self._isotopes = {} # The actual isotopes
        self.ions = ions
        self.ion = IonSet(self)

    # Isotope support
    def _getisotopes(self):
        L = self._isotopes.keys()
        L.sort()
        return L
    isotopes = property(_getisotopes,doc="List of all isotopes")
    def add_isotope(self,number):
        """
        Add an isotope for the element.
        """
        if number not in self._isotopes:
            self._isotopes[number] = Isotope(self,number)
        return self._isotopes[number]
    def __getitem__(self,number):
        return self._isotopes[number]

    def __iter__(self):
        """
        Process the elements in Z order
        """
        for isotope in self.isotopes:
            yield self._isotopes[isotope]

    # Note: using repr rather than str for the element symbol so
    # that lists of elements print nicely.  Since elements are
    # effectively singletons, the symbol name is the representation
    # of the instance.
    def __repr__(self):
        return self.symbol

    def __getstate__(self):
        """
        Can't pickle elements without breaking extensibility.
        Suppress it for now.
        """
        raise TypeError("cannot copy or pickle elements")

element_base = {
                # number: name symbol ions
    0: ['Neutron',     'n',  ()],
    1: ['Hydrogen',    'H',  (1,)],
    2: ['Helium',      'He', ()],
    3: ['Lithium',     'Li', (1,)],
    4: ['Beryllium',   'Be', (2,)],
    5: ['Boron',       'B',  (3,)],
    6: ['Carbon',      'C',  (2,-4,4)],
    7: ['Nitrogen',    'N',  (2,-3,3,4,5)],
    8: ['Oxygen',      'O',  (-2,)],
    9: ['Fluorine',    'F',  (-1,)],
    10: ['Neon',       'Ne', ()],
    11: ['Sodium',     'Na', (1,)],
    12: ['Magnesium',  'Mg', (2,)],
    13: ['Aluminum',   'Al', (3,)],
    14: ['Silicon',    'Si', (4,)],
    15: ['Phosphorus', 'P',  (-3,3,4,5)],
    16: ['Sulfur',     'S',  (-2,2,4,6)],
    17: ['Chlorine',   'Cl', (-1,1,3,5,7)],
    18: ['Argon',      'Ar', ()],
    19: ['Potassium',  'K',  (1,)],
    20: ['Calcium',    'Ca', (2,)],
    21: ['Scandium',   'Sc', (3,)],
    22: ['Titanium',   'Ti', (3,4)],
    23: ['Vanadium',   'V',  (2,3,4,5)],
    24: ['Chromium',   'Cr', (2,3,6)],
    25: ['Manganese',  'Mn', (2,3,4,6,7)],
    26: ['Iron',       'Fe', (2,3)],
    27: ['Cobalt',     'Co', (2,3)],
    28: ['Nickel',     'Ni', (2,3)],
    29: ['Copper',     'Cu', (1,2)],
    30: ['Zinc',       'Zn', (2,)],
    31: ['Gallium',    'Ga', (3,)],
    32: ['Germanium',  'Ge', (4,)],
    33: ['Arsenic',    'As', (-3,3,5)],
    34: ['Selenium',   'Se', (-2,4,6)],
    35: ['Bromine',    'Br', (-1,1,5)],
    36: ['Krypton',    'Kr', ()],
    37: ['Rubidium',   'Rb', (1,)],
    38: ['Strontium',  'Sr', (2,)],
    39: ['Yttrium',    'Y',  (3,)],
    40: ['Zirconium',  'Zr', (4,)],
    41: ['Niobium',    'Nb', (3,5)],
    42: ['Molybdenum', 'Mo', (2,3,4,5,6)],
    43: ['Technetium', 'Tc', (7,)],
    44: ['Ruthenium',  'Ru', (2,3,4,6,8)],
    45: ['Rhodium',    'Rh', (2,3,4)],
    46: ['Palladium',  'Pd', (2,4)],
    47: ['Silver',     'Ag', (1,)],
    48: ['Cadmium',    'Cd', (2,)],
    49: ['Indium',     'In', (3,)],
    50: ['Tin',        'Sn', (2,4)],
    51: ['Antimony',   'Sb', (-3,3,5)],
    52: ['Tellurium',  'Te', (-2,4,6)],
    53: ['Iodine',     'I',  (-1,1,5,7)],
    54: ['Xenon',      'Xe', ()],
    55: ['Cesium',     'Cs', (1,)],
    56: ['Barium',     'Ba', (2,)],
    57: ['Lanthanum',  'La', (3,)],
    58: ['Cerium',     'Ce', (3,4)],
    59: ['Praseodymium', 'Pr', (3,4)],
    60: ['Neodymium',  'Nd', (3,)],
    61: ['Promethium', 'Pm', (3,)],
    62: ['Samarium',   'Sm', (2,3)],
    63: ['Europium',   'Eu', (2,3)],
    64: ['Gadolinium', 'Gd', (3,)],
    65: ['Terbium',    'Tb', (3,4)],
    66: ['Dysprosium', 'Dy', (3,)],
    67: ['Holmium',    'Ho', (3,)],
    68: ['Erbium',     'Er', (3,)],
    69: ['Thulium',    'Tm', (2,3)],
    70: ['Ytterbium',  'Yb', (2,3)],
    71: ['Lutetium',   'Lu', (3,)],
    72: ['Hafnium',    'Hf', (4,)],
    73: ['Tantalum',   'Ta', (5,)],
    74: ['Tungsten',   'W',  (2,3,4,5,6)],
    75: ['Rhenium',    'Re', (-1,2,4,6,7)],
    76: ['Osmium',     'Os', (2,3,4,6,8)],
    77: ['Iridium',    'Ir', (2,3,4,6)],
    78: ['Platinum',   'Pt', (2,4)],
    79: ['Gold',       'Au', (1,3)],
    80: ['Mercury',    'Hg', (1,2)],
    81: ['Thallium',   'Tl', (1,3)],
    82: ['Lead',       'Pb', (2,4)],
    83: ['Bismuth',    'Bi', (3,5)],
    84: ['Polonium',   'Po', (2,4)],
    85: ['Astatine',   'At', (-1,1,3,5,7)],
    86: ['Radon',      'Rn', ()],
    87: ['Francium',   'Fr', (1,)],
    88: ['Radium',     'Ra', (2,)],
    89: ['Actinium',   'Ac', (3,)],
    90: ['Thorium',        'Th', (4,)],
    91: ['Protactinium',   'Pa', (4,5)],
    92: ['Uranium',        'U',  (3,4,5,6)],
    93: ['Neptunium',      'Np', (3,4,5,6)],
    94: ['Plutonium',      'Pu', (3,4,5,6)],
    95: ['Americium',      'Am', (3,4,5,6)],
    96: ['Curium',         'Cm', (3,)],
    97: ['Berkelium',      'Bk', (3,4)],
    98: ['Californium',    'Cf', (3,)],
    99: ['Einsteinium',    'Es', (3,)],
    100: ['Fermium',       'Fm', (3,)],
    101: ['Mendelevium',   'Md', (2,3)],
    102: ['Nobelium',      'No', (2,3)],
    103: ['Lawrencium',    'Lr', (3,)],
    104: ['Rutherfordium', 'Rf', (4,)],
    105: ['Dubnium',       'Db', ()],
    106: ['Seaborgium',    'Sg', ()],
    107: ['Bohrium',       'Bh', ()],
    108: ['Hassium',       'Hs', ()],
    109: ['Meitnerium',    'Mt', ()],
    110: ['Ununnilium',    'Uun', ()],
    111: ['Unununium',     'Uuu', ()],
    112: ['Ununbium',      'Uub', ()],
    114: ['Ununquadium',   'Uuq', ()],
    116: ['Ununhexium',    'Uuh', ()],
}

def default_table(table=None):
    """
    Return the default table unless a specific table has been requested.

    Used in a context like::

        def summary(table=None):
            table = core.default_table(table)
            ...
    """
    if table == None:
        import periodictable
        table = periodictable.elements
    return table

def define_elements(table, namespace):
    """
    Define external variables for each element in namespace.

    Elements are defined both by name and by symbol.

    Returns the list of names defined.

    This is called from __init__ as::

        elements = core.PeriodicTable()
        __all__  += core.define_elements(elements, globals())

    Note that this will only work namespace as globals(), not as locals()!
    """

    # Build the dictionary of element symbols
    names = {}
    for el in table:
        names[el.symbol] = el
        names[el.name] = el
    for el in [table.D,table.T]:
        names[el.symbol] = el
        names[el.name] = el

    # Copy it to the namespace
    for k,v in names.items():
        namespace[k] = v

    # return the keys
    return names.keys()