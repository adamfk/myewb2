
'''
good docs
http://docs.python.org/release/2.2.3/lib/re-objects.html
http://docs.python.org/release/2.2.3/lib/match-objects.html



some aggregate commands will be modified with a filter first to set the scope.

if you 

SUM[global]( )



'''

import re

cmd_pattern = re.compile( r"""  \s*
                                (?P<cmd>[A-Za-z]+)                                   #capture the command
                                (?:
                                    <\s*(?P<scope>[.]+)\s*>                          #not used as of now
                                ){0,1}
                                \(
                                    \s*
                                    (?P<program_area>[a-zA-Z_]+)        
                                    (?:
                                        \.
                                        (?P<field_group>[a-zA-Z_]+)                  #field group may not be there
                                    ){0,1}
                                    :
                                    (?P<field_name>[a-zA-Z_]+)
                                    \s*
                                    (?:                                              #non capturing group
                                        ,                                            #separator
                                        \s*                                    
                                        (?P<condition>[a-zA-Z_]+)                    #'if'
                                        \s+                                          #the separator NOTE THE '+'
                                        (?P<conditional_program_area>[a-zA-Z_]+)       #something like '='
                                        \s*
                                        (?:
                                            \.
                                            (?P<conditional_field_group>[a-zA-Z_]+)    #field group may not be there
                                        ){0,1}
                                        :
                                        (?P<conditional_any_field>[a-zA-Z_]+)         #something like '='
                                        \s*                                          #the separator NOTE THE '+'
                                        (?P<conditional_operator>[=!<>]{0,1})          #something like '='
                                        \s*
                                        (?P<conditional_value>[a-zA-Z_0-9]+)           #something like '1'
                                        \s*
                                    ){0,1}
                                \)
                                \s*
                                """, re.MULTILINE + re.VERBOSE)  

field_pattern = re.compile( r"\s*(?P<field_group>[a-zA-Z_]+):(?P<field_name>[a-zA-Z_]+)\s*", re.MULTILINE)
operation_pattern = re.compile( r"\s*(?P<op>[\+\-\*/])\s*", re.MULTILINE)
number_pattern = re.compile( r"\s*(?P<number>[0-9.]+)\s*", re.MULTILINE)


#----------------------------------------------
class ParseNumber():
    
    def __init__(self, value):
        self.value = float(value)


#----------------------------------------------
class ParseOperation():
    
    def __init__(self, operation):
        self.operation = operation

#----------------------------------------------
class ParseCommand():

    #scope used later on to define custom scope
    # possibly used to like: SUM[self](....), or SUM[global](....)
    #scope can be empty or None.    
    def __init__(self, command_name, program_area, field_group, field_name, scope, condition, conditional_program_area, conditional_field_group, conditional_any_field, conditional_operator, conditional_value):
        
        #TODO: put in check for valid command names
        
        self.command_name = command_name.lower()
        self.program_area = program_area
        self.field_group = field_group
        self.field_name = field_name    
        self.scope = scope.lower()
        
        self.condition = condition
        self.conditional_program_area = conditional_program_area
        self.conditional_field_group = conditional_field_group
        self.conditional_any_field = conditional_any_field
        self.conditional_operator = conditional_operator
        self.conditional_value = conditional_value


def parse_equation(input):

    start_index = 0
    end_index = len(input)
    
    result = list()
    failed = False
    found = False
      
    while failed == False and start_index < end_index:
        found = False #for looping
       
      
        #look for command pattern
        if found == False:
            g = cmd_pattern.match(input, start_index, end_index)
            if g:
                found = True
                cmd = g.group("cmd")
                program_area = g.group("program_area")        #case sensitive!
                field_group = g.group("field_group") or ""    #case sensitive!
                field_name = g.group("field_name")            #case sensitive!
                scope = g.group("scope") or "" #may be None
                scope = scope.lower()
                
                condition = g.group("condition") or "" #may be None
                conditional_program_area = g.group("conditional_program_area") or "" #may be None
                conditional_field_group = g.group("conditional_field_group") or "" #may be None
                conditional_any_field = g.group("conditional_any_field") or "" #may be None
                conditional_operator = g.group("conditional_operator") or "" #may be None
                conditional_value = g.group("conditional_value") or "" #may be None
                result.append(ParseCommand(cmd, program_area, field_group, field_name, scope, condition, conditional_program_area, conditional_field_group, conditional_any_field, conditional_operator, conditional_value)) #add in value
                start_index = g.end()
        
        #look for operation pattern
        if found == False:
            g = operation_pattern.match(input, start_index, end_index)
            if g:
                found = True
                operation = g.group("op")              
                result.append(ParseOperation(operation)) #add in value
                start_index = g.end()
        
        #look for number pattern
        if found == False:
            g = number_pattern.match(input, start_index, end_index)
            if g:
                found = True
                number = g.group("number")
                result.append(ParseNumber(number)) #add in value
                start_index = g.end()
        
        if found == False:
            failed = True 
            print "failed!"
            raise
        
    #end of while
    return result


input = "SUM( FN.evl:some_field, if FN:type_ft = 1 )"

#DEBUG!
print parse_equation(input)

sql = ""
#result = parse(input)

#
#print sql
#
#safe_dict = dict()
#print eval("8 * (2 + 3)", {"__builtins__":None},safe_dict) 
#
#print repr(result)  
#print "DOne\n\n\n"
#
##
#safe_dict = dict()
#print eval("8 *+-+* (2 + 3)", {"__builtins__":None},safe_dict)

