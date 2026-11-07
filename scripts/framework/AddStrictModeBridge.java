import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;
/** Bridge modern libcore's unbuffered-I/O notification into the legacy policy. */
public final class AddStrictModeBridge {
    public static void main(String[] args)throws Exception{
        ClassReader reader=new ClassReader(Files.readAllBytes(Paths.get(args[0])));
        ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_MAXS);
        reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
            @Override public void visitEnd(){
                MethodVisitor method=super.visitMethod(Opcodes.ACC_PUBLIC,"onUnbufferedIO","()V",null,null);
                method.visitCode();method.visitVarInsn(Opcodes.ALOAD,0);method.visitLdcInsn("Unbuffered I/O");
                method.visitMethodInsn(Opcodes.INVOKEVIRTUAL,"android/os/StrictMode$AndroidBlockGuardPolicy","onCustomSlowCall","(Ljava/lang/String;)V",false);
                method.visitInsn(Opcodes.RETURN);method.visitMaxs(0,0);method.visitEnd();super.visitEnd();
            }
        },0);
        Files.write(Paths.get(args[1]),writer.toByteArray());
    }
}
