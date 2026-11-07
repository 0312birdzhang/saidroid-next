public class JavaCli282MainBase {
    public static void main(String[] args) {
        if(!"yes".equals(System.getProperty("cli.inherited.ready")))
            throw new AssertionError("Requested application's class initializer did not run before inherited main");
        System.out.println("JAVA_CLI282_INHERITED=PASS|initialized=true");
    }
}
