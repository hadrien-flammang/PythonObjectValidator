'''
    py_validator is a library that allows to validate a given data against an expected scheme.
    The given data and the expected scheme are both python's objects.
    If the expectation is not reached, the validation returns some explanations.

    More precisely, the validation function returns a pair : ( output data , set of tuples ).
    - The output data is essentially a deep copy of the input data.
        We will see further, how the input and output data may differ.

    - A tuple may be a pair ( <path> , <message> ) or a triple ( <path> , <message> , <value> )
        - <path>    is a string giving the localization of the the unmatched entry within the scheme.
        - <message> is a string giving an explanation about the error.
        - <value>   is a python's object giving the erroneous value (which is not always possible).

    Beware : the order of the error messages is unpredictable.

    The continuation of the documentation is given as samples of code in the function _code_sample :

    (c) H.Flammang / Viaccess-Orca - June 2023
'''
def _code_sample ():
    # from py_validator import *             <---- add this line (uncommented) in your code
    ''' Let's start with easy samples : '''
    scheme  = { 'name' : str               , 'age' : float } # expect a dict with 2 entries : "name" which must be a str and "age" which must be a float
    person1 = { 'name' : 'Arthur Dent'     , 'age' : 42    } # ok (42 is an int but also a float)
    person2 = { 'name' : 'Marvin'          , 'age' : None  } # invalid age (None is not an float)
    person3 = { 'name' : 'Tricia Mc Millan', 'age' : 35.5  , 'aka' : 'Trillian' , 'actress' : 'Z.Deschanel' } # superfluous keys
    person4 = { 'name' : False             } # invalid name (not a string) + missing key 'age'

    output,errors = validate( person1,scheme )
    assert output == person1 # the output data == the input data
    assert not errors        # when there is no error, errors is an empty set

    # let's examine our first error:
    output,errors = validate( person2,scheme )
    assert errors == {('.age','not a float',None)} # error triple
    #  unmatched entry ___^        ^          ^
    #  explanation ________________|          |
    #  erroneous value _______________________|

    output,errors = validate( person3,scheme ) # parameter ignore_extra_keys is False by default
    assert len( errors ) == 2 # 2 errors : one for each extra key, but order is unpredictable
    assert errors == {('','extra key','actress'),('','extra key','aka')} # 2 extra keys detected
    assert 'aka' not in output and 'actress' not in output # the extra keys are no more present in the output

    output,errors = validate( person3,scheme,True ) # set ignore_extra_keys to True
    assert not errors
    assert 'aka' in output and 'actress' in output # the extra keys are still present in the output
    assert not validate( output,person3 )[1]    # use the validator to deep compare the 2 python's objects !
    # the short cut "assert not validate(obj,scheme)[1]" is a little bit confusing, but it means that it is well validated.
    # remember that validate(...)[1] is actually the set of errors

    output,errors = validate( person4,scheme ) # remember that errors is a set.
    assert errors == {('','not found','age'),('.name','not a str',False )}

    ''' Let's check some other types : '''
    assert not validate( u'zeta:\u03B6',str )[1] # unicode strings are welcome (for python 2 lovers)
    assert not validate( 123,123   )[1]          # validate equality of values (a little bit overkill)
    assert not validate( 123,int   )[1]          # validate a single typed value
    assert not validate( 123,float )[1]          # because an int is also a float (see below)
    assert not validate( [[[1]]],[[[int]]] )[1]  # validate nested lists
    assert not validate( [1,.7,True,None],[int,float,bool,None] )[1] # validate a typed list

    ''' Because an int may match a float, in the following case, the output is not the input :'''
    output,errors = validate( 123,float ) # in this case the output is not exactly the input
    assert type( output ) == float        # beware : for python 123 == 123.0, but type( 123 ) != type( 123.0 )
    assert output == 123.0                # output is float value of the input
    assert not errors

    ''' Let's try our first functional checking : '''
    check_presence = lambda x : True # a tricky way to just check the presence of an entry
    def check_name_case ( s ):
        import re # we need regexp just here
        return re.match( '^[A-Z][a-z]*$',s )

    scheme = { 'name' : check_name_case , 'age' : check_presence }
    zaphod = { 'name' : 'Beeblebrox'    , 'age' : NotImplemented }
    tricia = { 'name' : 'McMillan'      }
    output,errors = validate( zaphod,scheme )
    assert not errors
    output,errors = validate( tricia,scheme )
    assert errors == {('.name','invalidated by check_name_case', 'McMillan'),('','not found','age')}

    ''' Use Or and And to create complex validation.
        Use Optional to create an optional key.
        Use ListOf to validate each element of a list.
        Use a lambda (or any function) to create more complex validation : '''
    def check_year ( y ) : return 1850 < y < 2023 # check a possible year of birth

    child_scheme  = { 'forename'             : str ,
                      Optional('name')       : str ,
                      'age'                  : Or( int,float )}

    person_scheme = { 'forename'             : str ,
                      'name'                 : str ,
                      'birth_year'           : And( int,check_year ),
                      Optional('death_year') : And( int,check_year ), # can't check death > birth now, but wait for it...
                      'children'             : ListOf( child_scheme )}

    charlot = { 'forename'   : 'Charles Spencer',
                'name'       : 'Chaplin'        ,
                'birth_year' : 1889             ,
                'death_year' : 1977             ,
                'children'   : [
                                { 'forename' : 'Geraldine'  , 'name' : 'Leigh'  , 'age' : 78   },
                                { 'forename' : 'Michael'    ,                     'age' : 77   },
                                { 'forename' : 'Josephine'  , 'name' : 'Gardin' , 'age' : 74.5 },
                                { 'forename' : 'Christopher',                     'age' : 60   },
                               ] }
    output,errors = validate( charlot,person_scheme )
    assert output == charlot
    assert not errors

    ''' Let's modify the data to see some errors: '''
    charlot['birth_year'] = 1789
    output,errors = validate( charlot,person_scheme )
    assert output == charlot
    assert errors == {('.birth_year','invalidated by check_year',1789)}
    # the function's name appears in the error message --^
    # with lambdas, the name is always <lambda>

    charlot['children'][2]['age'] = None
    output,errors = validate( charlot,person_scheme )
    assert output == charlot
    assert errors == {('.birth_year','invalidated by check_year',1789),('.children[2].age','not a float',None)}

    del charlot['children'][2]['age']
    output,errors = validate( charlot,person_scheme )
    assert output == charlot
    assert errors == {('.birth_year','invalidated by check_year',1789),('.children[2]','not found','age')}

    charlot['children'][1]['name'] = False
    charlot['children'][2]['age']  = 74
    output,errors = validate( charlot,person_scheme )
    assert output == charlot
    assert errors == {('.children[1].name','not a str',False),('.birth_year','invalidated by check_year',1789)}

    ''' And now, let's see some tricks with the checking function :
        The function used to check a value may also replace it.
        Return a ForceValue to replace the input value :    '''
    scheme = { 'age' : lambda n : ForceValue( n*2 ) }
    input  = { 'age' : 44 }
    output,errors = validate( input,scheme )
    assert input != output # this is a case where output != input
    assert output['age'] == 88
    assert not errors

    ''' The function used to check a value may also return an error message.
        Return an Error to set a customized error message.'''
    scheme = { 'age' : lambda n : True if n > 0 else Error('an age is always positive!') }
    data,errors = validate( {'age':44},scheme )
    assert not errors

    data,errors = validate( {'age':-44},scheme )
    assert errors == {('.age','an age is always positive!',-44 )}

    ''' The function used to check a value may also take the path of the current key as first parameter. '''
    def check ( path,value ):
        if 'year' in path and value > 2030 : return Error('invalid year' )
        if 'age'  in path and value < 0 : return Error('age must be positive')
        return True

    scheme = { 'age' : check , 'age_of_child' : check , 'year_of_birth' : check , 'year_of_wedding' : check }
    errors = validate({ 'age' : 49 , 'age_of_child' : 9 , 'year_of_birth' : 1931 , 'year_of_wedding' : 1964 },scheme )[1]
    assert not errors

    errors = validate({ 'age' : 49 , 'age_of_child' : -9 , 'year_of_birth' : 2931 , 'year_of_wedding' : 1964 },scheme )[1]
    assert errors == {('.age_of_child','age must be positive',-9),('.year_of_birth','invalid year',2931)}

    ''' And last but not least, use a context in order to cross-check values : '''
    class DateChecker :
        def __init__(self):
            self.birth = self.death = None
        def reset (self):
            self.birth = self.death = None
        def __call__ (self,path,year):
            if year <= 1800 : return Error('invalid year')
            if 'death' in path :
                self.death = year  # because we can't predict their order...
                if self.birth and self.birth > year : return Error('death must be after birth')
            elif 'birth' in path :
                self.birth = year  # ...wait that both dates are stored to compare them
                if self.death and self.death < year : return Error('birth must be before death')
            return True

    date_checker = DateChecker()
    person_scheme['birth_year'] = date_checker # change the function that checks dates
    person_scheme['death_year'] = date_checker
    del charlot['children'][1]['name'] # restore the correct values
    charlot['birth_year'] = 1889
    output,errors = validate( charlot,person_scheme )
    assert not errors

    date_checker.reset() # don't forget to reset the context
    charlot['birth_year'] = 2010 # set birth after death
    output,errors = validate( charlot,person_scheme )
    assert len( errors ) == 1
    assert errors.issubset({('.birth_year','birth must be before death',2010),('.death_year','death must be after birth',1977)})

    ''' At the end of the day, a validation function may be :
         - a lambda
         - a function (defined with "def")
         - a method of a class
         - an instance of a class (method "__call__" is called)
        It may take :
         - 1 parameter   : the value to be validated
         - 2 parameters  : the path to the value and the value to be validated
        It may return :
         - a Error       : give a customized error message
         - a ForceValue  : give a value that overwrite the original -> the value is treated as validated
         - anything else : if its boolean value is False, a generic error message is generated '''

    ''' A nice tool to access to a value by its path :'''
    def read_data ( data,path ):
        if not path : return data
        if path.startswith('.') :
            key = path[1:].split('[')[0].split('.')[0]
            return read_data( data[key],path[len(key)+1:] )
        if path.startswith('[') :
            key = path[1:].split(']')[0]
            return read_data( data[int(key)],path[len(key)+2:] )

    assert read_data( charlot,'.children[0].age' ) == 78

    ''' An other nice trick : if you want to keep order of keys, you can use OrderedDict :'''
    def json2ordered ( json_str ):
        import json,collections
        return json.loads( json_str,object_pairs_hook=collections.OrderedDict )

    def json2dict ( json_str ):
        import json
        return json.loads( json_str )

    scheme     = eval( '{' + ','.join( '"key%d":int'%i for i in range( 10 )) + '}' )
    json_str   = '{' + ','.join( '"key%d":0'%i for i in range( 10 )) + '}'
    assert not validate( json2dict( json_str ),scheme )[1]
    assert not validate( json2ordered( json_str ),scheme )[1]
    # useless for latest versions of python 3 since dict are then natively ordered.

    print('py_validator auto test is successful')

########################################################################################################################

class Or :
    def __init__(self,*choice):
        self.choice = choice

class And:
    def __init__(self,*choice):
        self.choice = choice

class ListOf:
    def __init__(self,check):
        self.check = check

class Optional:
    def __init__(self,key):
        self.key = key

class ForceValue:
    def __init__(self,value):
        self.value = value

class Error:
    def __init__(self,message):
        self.message = message

def validate ( given,expected,ignore_extra_keys=False ):

    ispy3    = (lambda x : [ 0 for x in [0]] and x )( 1 )
    strtype  = (str,) if ispy3 else (str,unicode)  # save python 2 compatibility
    isDict   = lambda x : hasattr( x,'items' ) and hasattr( x,'keys' )
    isFunc   = lambda x : callable( x ) and not isinstance( x,type )
    isList   = lambda x : isinstance( x,(list,tuple,set,frozenset))
    isOpt    = lambda x : isinstance( x,Optional )
    isListOf = lambda x : isinstance( x,ListOf )
    isType   = lambda x : isinstance( x,type )
    isAnd    = lambda x : isinstance( x,And )
    isOr     = lambda x : isinstance( x,Or )
    funcInfo = lambda f : (f.__code__.co_argcount-int(f.__class__!=type(lambda:0)),f.__code__.co_name) if hasattr(f,'__code__') else funcInfo(f.__call__)
    # ^-- funcInfo(f) returns (arity,name) of the function f (tricky one based on powerful python's introspection)

    def sub ( obj,exp,report,path ):
        try :
            if obj == exp : return obj
            if ( isOr( exp ) or isAnd( exp ) ) and not exp.choice :
                report.append((path,'empty choice'))
            elif isOr( exp ) :
                for c in exp.choice :                   # Or( X,Y,Z ) fails if all X,Y and Z fails
                    report2 = []                        # In such a case, the error report contains
                    obj2    = sub( obj,c,report2,path ) # only the failure of Z (the last one)
                    if not report2 : break
                if report2 : report.extend( report2 )
                else       : obj = obj2
            elif isAnd( exp ) :
                for c in exp.choice :                   # And( X,Y,Z ) fails if any of X,Y or Z fails
                    report2 = []                        # In such a case, the error report contains
                    obj2    = sub( obj,c,report2,path ) # the failure of the first which failed.
                    if report2 : break
                if report2 : report.extend( report2 )
                else       : obj = obj2
            elif isList( exp ) :
                if not isList( obj ) :
                    report.append((path,'array expected',obj))
                elif len( exp ) != len( obj ):
                    report.append((path,'length is %d but should be %d'%( len( obj ),len( exp )),obj ))
                else :
                    obj = [sub( o,e,report,path+'[%d]'%i ) for i,(o,e) in enumerate( zip( obj,exp ))]
            elif isListOf( exp ) :
                obj = [sub( o,exp.check,report,path+'[%d]'%i ) for i,o in enumerate( obj )]
            elif isDict( exp ) :
                if not isDict( obj ) :
                    report.append((path,'dictionary expected',obj))
                else:
                    keys,obj2 = [],{}
                    for expk,expv in exp.items():
                        key,mandatory = (expk.key,False) if isOpt( expk ) else (expk,True)
                        keys.append( key )
                        if key in obj :
                            obj2[key] = sub( obj[key],expv,report,path+'.'+key )
                        elif mandatory :
                            report.append( (path,'not found',key))
                    extra = set( obj.keys()) - set( keys )
                    if extra :
                        if ignore_extra_keys :
                            for key in extra :
                                obj2[key] = obj[key]
                        else:
                            report.extend( (path,'extra key',e) for e in extra )
                    obj = obj2
            elif isFunc( exp ) :
                nb,name = funcInfo( exp )
                if nb not in (1,2) :
                    report.append((path,name+' should take 1 or 2 parameters'))
                else:
                    try :
                        res = exp( obj ) if nb == 1 else exp( path,obj )
                    except Exception as e :
                        report.append((path,'%s call raised %s'%( name,e )))
                    else:
                        if isinstance( res,ForceValue ) :
                            obj = res.value
                        elif isinstance( res,Error ) :
                            report.append((path,res.message,obj))
                        elif not res :
                            report.append((path,'invalidated by %s'%name,obj))
            elif isType( exp ) :
                if exp == float and type( obj ) == int :
                    obj = float( obj ) # special case : an int shall match a float
                elif exp in strtype :
                    if not isinstance( obj,strtype ) :
                        report.append((path,'not a str',obj ))
                elif exp != type( obj ) :
                    report.append((path,'not a '+exp.__name__,obj ))
            elif exp != obj :
                report.append((path,'!= %s'%exp,obj ))
        except Exception as e :
            report.append((path,'failure',e ))
        return obj

    report = []
    return sub( given,expected,report,'' ),set( report )

if __name__ == '__main__':
    _code_sample()
