import org.hamcrest.*;
/** Diagnostic for genuine platform Hamcrest dispatch and JUnit assumptions. */
public final class HamcrestDispatchContract {
    static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    static final SelfDescribing VALUE=new SelfDescribing(){public void describeTo(Description d){
        check(d!=null,"SelfDescribing received null Description");
        System.out.println("DESCRIPTION_CALLBACK=actual|class="+d.getClass().getName());
        d.appendText("literal-description");
    }};
    static void failure(String label,Throwable t){
        System.out.println(label+"=FAIL|type="+t.getClass().getName());
        for(StackTraceElement e:t.getStackTrace())System.out.println("  "+e.toString());
        try{System.out.println("message="+t.getMessage());}catch(Throwable secondary){System.out.println("message_error="+secondary.getClass().getName());}
    }
    public static void main(String[] args)throws Exception{
        int errors=0;
        java.nio.file.Files.write(java.nio.file.Paths.get("maps.txt"),java.nio.file.Files.readAllBytes(java.nio.file.Paths.get("/proc/self/maps")));
        for(java.lang.reflect.Method m:StringDescription.class.getMethods())if(m.getName().equals("appendDescriptionOf")||m.getName().equals("toString"))System.out.println("DESCRIPTION_METHOD="+m.toGenericString());
        try{StringDescription d=new StringDescription();check(d.appendText("a")==d,"appendText identity");check(d.toString().equals("a"),"appendText value");System.out.println("DIRECT_DESCRIPTION=PASS");}catch(Throwable t){errors++;failure("DIRECT_DESCRIPTION",t);}
        try{StringDescription d=new StringDescription();check(d.appendDescriptionOf(VALUE)==d,"appendDescriptionOf identity");check(d.toString().equals("literal-description"),"appendDescriptionOf value");System.out.println("SELF_DESCRIPTION=PASS");}catch(Throwable t){errors++;failure("SELF_DESCRIPTION",t);}
        try{check(StringDescription.asString(VALUE).equals("literal-description"),"static description");System.out.println("STATIC_DESCRIPTION=PASS");}catch(Throwable t){errors++;failure("STATIC_DESCRIPTION",t);}
        try{Throwable e=(Throwable)Class.forName("org.junit.internal.AssumptionViolatedException").getConstructor(String.class).newInstance("literal-assumption");check(e.getMessage().contains("literal-assumption"),"assumption message");System.out.println("ASSUMPTION_MESSAGE=PASS");}catch(ClassNotFoundException t){System.out.println("ASSUMPTION_MESSAGE=UNAVAILABLE|platform_has_no_JUnit4_class=true");}catch(Throwable t){errors++;failure("ASSUMPTION_MESSAGE",t);}
        check(errors==0,"Diagnostic failures "+errors);System.out.println("HAMCREST_DISPATCH=PASS");
    }
}
