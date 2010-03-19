import re, copy

class IfcSchema:
    SIMPLETYPES = ["INTEGER", "REAL", "STRING", "NUMBER", "LOGICAL", "BOOLEAN"]
    NO_ATTR = ["WHERE", "INVERSE","WR2","WR3", "WR4", "WR5", "UNIQUE", "DERIVE"]

    def __init__(self, filename):
        self.filename = filename
        self.file = open(self.filename)
        self.data = self.file.read()
        self.types = self.readTypes()
        self.entities = self.readEntities()
        print "Parsed from schema %s: %s entities and %s types" % (self.filename, len(self.entities), len(self.types))

    def readTypes(self):
        """
        Parse all the possible types from the schema, 
        returns a dictionary Name -> Type
        """
        types = {}
        for m in re.finditer("TYPE (.*) = (.*);", self.data):
            typename, typetype = m.groups() 
            if typetype in self.SIMPLETYPES:
                types[typename] = typetype
            else:
                types[typename] = "#" + typetype
                
        return types
        
    def readEntities(self):
        """
        Parse all the possible entities from the schema,
        returns a dictionary of the form:
        { name: { 
            "supertype": supertype, 
            "attributes": [{ key: value }, ..]
        }}  
        """
        entities = {}
        
        # Regexes must be greedy to prevent matching outer entity and end_entity strings
        # Regexes have re.DOTALL to match newlines
        for m in re.finditer("ENTITY (.*?)END_ENTITY;", self.data, re.DOTALL):
            entity = {}
            raw_entity_str = m.groups()[0]

            entity["name"] = re.search("(.*?)[;|\s]", raw_entity_str).groups()[0].upper()

            subtypeofmatch = re.search(".*SUBTYPE OF \((.*?)\);", raw_entity_str)
            entity["supertype"] = subtypeofmatch.groups()[0].upper() if subtypeofmatch else None

            # find the shortest string matched from the end of the entity type header to the
            # first occurence of a NO_ATTR string (when it occurs on a new line)
            inner_str = re.search(";(.*?)$", raw_entity_str, re.DOTALL).groups()[0]            

            attrs_str = min([inner_str.partition("\r\n "+a)[0] for a in self.NO_ATTR])
            attrs = []
            for am in re.finditer("(.*?) : (.*?);", attrs_str, re.DOTALL):
                name, attr_type = [s.replace("\r\n\t","") for s in am.groups()]
                attrs.append((name, attr_type))
            
            entity["attributes"] = attrs
            entities[entity["name"]] = entity
        

        return entities

    def getAttributes(self, name):
        """
        Get all attributes af an entity, including supertypes
        """
        ent = self.entities[name]

        attrs = []
        while ent != None:
            this_ent_attrs = copy.copy(ent["attributes"])
            this_ent_attrs.reverse()
            attrs.extend(this_ent_attrs)
            ent = self.entities.get(ent["supertype"], None)

        attrs.reverse()
        return attrs
        

if __name__ == "__main__":
    schema = IfcSchema("IFC2X3_TC1.exp")

