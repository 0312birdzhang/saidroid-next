import java.io.File;
import java.util.*;
import org.jf.dexlib2.*;
import org.jf.dexlib2.iface.*;
import org.jf.dexlib2.base.reference.BaseTypeReference;
import org.jf.dexlib2.immutable.*;
import org.jf.dexlib2.immutable.reference.ImmutableMethodReference;
import org.jf.dexlib2.builder.MutableMethodImplementation;
import org.jf.dexlib2.builder.instruction.*;
import org.jf.dexlib2.writer.pool.DexPool;
import org.jf.dexlib2.writer.io.FileDataStore;

/** Legacy framework Boolean primitive overload delegates to modern libcore's real setter. */
public final class AddDateFormatBridge {
    private static final class Adapted extends BaseTypeReference implements ClassDef {
        final ClassDef original;final Method bridge;
        Adapted(ClassDef original,Method bridge){this.original=original;this.bridge=bridge;}
        public String getType(){return original.getType();}public int getAccessFlags(){return original.getAccessFlags();}public String getSuperclass(){return original.getSuperclass();}public List<String>getInterfaces(){return original.getInterfaces();}public String getSourceFile(){return original.getSourceFile();}public Set<? extends Annotation>getAnnotations(){return original.getAnnotations();}
        public Iterable<? extends Field>getStaticFields(){return original.getStaticFields();}public Iterable<? extends Field>getInstanceFields(){return original.getInstanceFields();}public Iterable<? extends Field>getFields(){return original.getFields();}
        public Iterable<? extends Method>getDirectMethods(){List<Method> result=new ArrayList<Method>();for(Method m:original.getDirectMethods())result.add(m);result.add(bridge);return result;}
        public Iterable<? extends Method>getVirtualMethods(){return original.getVirtualMethods();}
        public Iterable<? extends Method>getMethods(){List<Method>result=new ArrayList<Method>();for(Method m:original.getMethods())result.add(m);result.add(bridge);return result;}
    }
    public static void main(String[] args)throws Exception{
        DexFile original=DexFileFactory.loadDexFile(new File(args[0]),Opcodes.forApi(30));DexPool pool=new DexPool(Opcodes.forApi(30));boolean found=false;
        for(ClassDef definition:original.getClasses()){
            if(!definition.getType().equals("Ljava/text/DateFormat;")){pool.internClass(definition);continue;}
            boolean actual=false;
            for(Method method:definition.getMethods())if(method.getName().equals("set24HourTimePref")){
                if(method.getParameterTypes().equals(Arrays.asList("Ljava/lang/Boolean;")))actual=true;
                if(method.getParameterTypes().equals(Arrays.asList("Z")))throw new IllegalStateException("Bridge already exists");
            }
            if(!actual)throw new IllegalStateException("Real DateFormat Boolean setter absent");
            MutableMethodImplementation code=new MutableMethodImplementation(1);
            code.addInstruction(new BuilderInstruction35c(Opcode.INVOKE_STATIC,1,0,0,0,0,0,new ImmutableMethodReference("Ljava/lang/Boolean;","valueOf",Arrays.asList("Z"),"Ljava/lang/Boolean;")));
            code.addInstruction(new BuilderInstruction11x(Opcode.MOVE_RESULT_OBJECT,0));
            code.addInstruction(new BuilderInstruction35c(Opcode.INVOKE_STATIC,1,0,0,0,0,0,new ImmutableMethodReference("Ljava/text/DateFormat;","set24HourTimePref",Arrays.asList("Ljava/lang/Boolean;"),"V")));
            code.addInstruction(new BuilderInstruction10x(Opcode.RETURN_VOID));
            Method bridge=new ImmutableMethod(definition.getType(),"set24HourTimePref",Arrays.asList(new ImmutableMethodParameter("Z",Collections.<Annotation>emptySet(),"preference")),"V",AccessFlags.PUBLIC.getValue()|AccessFlags.STATIC.getValue(),Collections.<Annotation>emptySet(),Collections.<HiddenApiRestriction>emptySet(),code);
            pool.internClass(new Adapted(definition,bridge));found=true;
        }
        if(!found)throw new IllegalStateException("DateFormat absent");
        FileDataStore store=new FileDataStore(new File(args[1]));try{pool.writeTo(store);}finally{store.close();}
        DexFile result=DexFileFactory.loadDexFile(new File(args[1]),Opcodes.forApi(30));
        if(result.getClasses().size()!=original.getClasses().size())throw new AssertionError("Core class inventory changed");
        // dexlib2 2.5 undercounts outgoing words for invoke-custom/polymorphic.
        // Their encoded register count is authoritative (including wide words).
        // Preserve every instruction and repair only code_item.outs_size.
        java.lang.reflect.Field offset=org.jf.dexlib2.dexbacked.DexBackedMethodImplementation.class.getDeclaredField("codeOffset");offset.setAccessible(true);
        int repaired=0;
        try(java.io.RandomAccessFile file=new java.io.RandomAccessFile(args[1],"rw")){
            for(ClassDef c:result.getClasses())for(Method m:c.getMethods()){
                MethodImplementation impl=m.getImplementation();if(impl==null)continue;
                int words=0;
                for(org.jf.dexlib2.iface.instruction.Instruction instruction:impl.getInstructions())
                    if(instruction.getOpcode().name.startsWith("invoke-")&&instruction instanceof org.jf.dexlib2.iface.instruction.VariableRegisterInstruction)
                        words=Math.max(words,((org.jf.dexlib2.iface.instruction.VariableRegisterInstruction)instruction).getRegisterCount());
                int at=offset.getInt(impl)+4;file.seek(at);int old=file.readUnsignedByte()|(file.readUnsignedByte()<<8);
                if(old<words){file.seek(at);file.write(words&255);file.write(words>>>8);repaired++;}
            }
        }
        byte[] bytes=java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(args[1]));
        byte[] digest=java.security.MessageDigest.getInstance("SHA-1").digest(Arrays.copyOfRange(bytes,32,bytes.length));System.arraycopy(digest,0,bytes,12,20);
        java.util.zip.Adler32 checksum=new java.util.zip.Adler32();checksum.update(bytes,12,bytes.length-12);long sum=checksum.getValue();for(int i=0;i<4;i++)bytes[8+i]=(byte)(sum>>>(8*i));
        java.nio.file.Files.write(java.nio.file.Paths.get(args[1]),bytes);
        System.out.println("DEX_OUTGOING_WORDS=repaired|methods="+repaired);
        System.out.println("DATE_FORMAT_BRIDGE=PASS|classes="+result.getClasses().size());
    }
}
