public final class JavaCli268ReturnMain {
    public static void main(String[] args) {
        if(args.length!=1||!args[0].equals("argument-preserved"))throw new AssertionError("argument");
        System.out.println("JAVA_CLI268_RETURN=PASS");
    }
}
