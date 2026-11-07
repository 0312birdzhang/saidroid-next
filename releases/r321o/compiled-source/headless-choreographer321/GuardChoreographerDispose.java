import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import org.jf.dexlib2.*;
import org.jf.dexlib2.iface.*;
import org.jf.dexlib2.iface.instruction.*;
import org.jf.dexlib2.iface.reference.*;
import org.jf.dexlib2.iface.value.*;
import org.jf.dexlib2.immutable.*;
import org.jf.dexlib2.builder.*;
import org.jf.dexlib2.builder.instruction.*;
import org.jf.dexlib2.writer.pool.DexPool;
import org.jf.dexlib2.writer.io.FileDataStore;
import org.jf.baksmali.*;
import org.jf.baksmali.Adaptors.ClassDefinition;
import org.jf.baksmali.formatter.BaksmaliWriter;

/** One-method DEX overlay; no D8 framework compilation or bucket repartition. */
public final class GuardChoreographerDispose {
    private static final String TYPE="Landroid/view/Choreographer;";
    private static final String RECEIVER="Landroid/view/Choreographer$FrameDisplayEventReceiver;";
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static String key(Method m){return m.getDefiningClass()+"->"+m.getName()+m.getParameterTypes()+m.getReturnType();}
    private static String render(ClassDef c)throws IOException{
        BaksmaliOptions options=new BaksmaliOptions();options.apiLevel=29;options.accessorComments=false;
        StringWriter text=new StringWriter();BaksmaliWriter writer=new BaksmaliWriter(text);
        ClassDefinition definition=new ClassDefinition(options,c);definition.writeTo(writer);writer.flush();
        require(!definition.hadValidationErrors(),"smali validation: "+c.getType());return text.toString();
    }
    private static String withoutDispose(String text){
        String pattern="(?s)\\.method [^\\n]* dispose\\(\\)V\\n.*?\\.end method";
        require(text.split(pattern,-1).length==2,"exactly one dispose method");return text.replaceFirst(pattern,"DISPOSE_BODY");
    }
    private static boolean typedDefault(String t,EncodedValue v){switch(t.charAt(0)){case 'Z':return v instanceof BooleanEncodedValue&&!((BooleanEncodedValue)v).getValue();case 'B':return v instanceof ByteEncodedValue&&((ByteEncodedValue)v).getValue()==0;case 'S':return v instanceof ShortEncodedValue&&((ShortEncodedValue)v).getValue()==0;case 'C':return v instanceof CharEncodedValue&&((CharEncodedValue)v).getValue()==0;case 'I':return v instanceof IntEncodedValue&&((IntEncodedValue)v).getValue()==0;case 'J':return v instanceof LongEncodedValue&&((LongEncodedValue)v).getValue()==0;case 'F':return v instanceof FloatEncodedValue&&Float.floatToRawIntBits(((FloatEncodedValue)v).getValue())==0;case 'D':return v instanceof DoubleEncodedValue&&Double.doubleToRawLongBits(((DoubleEncodedValue)v).getValue())==0;case 'L':case '[':return v instanceof NullEncodedValue;default:return false;}}
    private static String value(EncodedValue v){if(v==null)return "absent";if(v instanceof BooleanEncodedValue)return "VALUE_BOOLEAN:"+((BooleanEncodedValue)v).getValue();if(v instanceof ByteEncodedValue)return "VALUE_BYTE:"+((ByteEncodedValue)v).getValue();if(v instanceof IntEncodedValue)return "VALUE_INT:"+((IntEncodedValue)v).getValue();if(v instanceof NullEncodedValue)return "VALUE_NULL";return "type="+v.getValueType()+":"+v;}
    private static ClassDef restoreTypedDefaults(ClassDef before,ClassDef after,List<String> omissions){
        List<Field> x=new ArrayList<Field>(),y=new ArrayList<Field>(),restored=new ArrayList<Field>();
        for(Field f:before.getStaticFields())x.add(f);for(Field f:after.getStaticFields())y.add(f);
        require(x.size()==y.size(),"static field count");boolean removed=false;
        for(int i=0;i<x.size();i++){
            Field f=x.get(i),g=y.get(i);require(f.getName().equals(g.getName())&&f.getType().equals(g.getType()),"field order");
            EncodedValue v=f.getInitialValue(),w=g.getInitialValue();
            if(!Objects.equals(v,w)){
                require(v!=null&&w==null&&typedDefault(f.getType(),v),"nondefault field delta "+f);removed=true;
                omissions.add(after.getType()+"\t"+f.getName()+"\t"+f.getType()+"\t"+i+"\t"+x.size()+"\t"+value(v)+"\t"+value(w));
            }
            if(removed)require(w==null,"not trailing omitted suffix");
            restored.add(new ImmutableField(g.getDefiningClass(),g.getName(),g.getType(),g.getAccessFlags(),v,g.getAnnotations(),g.getHiddenApiRestrictions()));
        }
        return new ImmutableClassDef(after.getType(),after.getAccessFlags(),after.getSuperclass(),after.getInterfaces(),after.getSourceFile(),after.getAnnotations(),restored,after.getInstanceFields(),after.getDirectMethods(),after.getVirtualMethods());
    }
    private static int codeOffset(MethodImplementation code)throws Exception{
        java.lang.reflect.Field f=org.jf.dexlib2.dexbacked.DexBackedMethodImplementation.class.getDeclaredField("codeOffset");f.setAccessible(true);return f.getInt(code);
    }
    public static void main(String[] args)throws Exception{
        File input=new File(args[0]),output=new File(args[1]);require(!output.exists(),"output already exists");
        Opcodes opcodes=Opcodes.forApi(29);DexFile before=DexFileFactory.loadDexFile(input,opcodes);
        byte[] original=Files.readAllBytes(input.toPath());require(original[4]=='0'&&original[5]=='3'&&original[6]=='9',"expected DEX039");
        Map<String,ClassDef> originalClasses=new TreeMap<String,ClassDef>();
        Map<String,String> text=new TreeMap<String,String>();Map<String,Integer> outgoing=new HashMap<String,Integer>();
        ByteBuffer old=ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN);
        DexPool pool=new DexPool(opcodes);int patched=0,methods=0;
        for(ClassDef c:before.getClasses()){
            text.put(c.getType(),render(c));originalClasses.put(c.getType(),c);
            for(Method m:c.getMethods())if(m.getImplementation()!=null)outgoing.put(key(m),(int)old.getShort(codeOffset(m.getImplementation())+4)&65535);
            if(!c.getType().equals(TYPE)){pool.internClass(c);continue;}
            ArrayList<Method> direct=new ArrayList<Method>();
            for(Method m:c.getDirectMethods()){
                if(!m.getName().equals("dispose")||!m.getParameterTypes().isEmpty()||!m.getReturnType().equals("V")){direct.add(m);continue;}
                MethodImplementation code=m.getImplementation();ArrayList<Instruction> instructions=new ArrayList<Instruction>();
                for(Instruction i:code.getInstructions())instructions.add(i);
                require(instructions.size()==3&&instructions.get(0).getOpcode()==Opcode.IGET_OBJECT&&instructions.get(1).getOpcode()==Opcode.INVOKE_VIRTUAL&&instructions.get(2).getOpcode()==Opcode.RETURN_VOID,"unexpected baseline dispose body");
                FieldReference field=(FieldReference)((ReferenceInstruction)instructions.get(0)).getReference();
                MethodReference call=(MethodReference)((ReferenceInstruction)instructions.get(1)).getReference();
                int register=((TwoRegisterInstruction)instructions.get(0)).getRegisterA();
                require(field.getDefiningClass().equals(TYPE)&&field.getName().equals("mDisplayEventReceiver")&&field.getType().equals(RECEIVER),"unexpected receiver field");
                require(call.getDefiningClass().equals(RECEIVER)&&call.getName().equals("dispose")&&call.getParameterTypes().isEmpty()&&call.getReturnType().equals("V")&&((FiveRegisterInstruction)instructions.get(1)).getRegisterC()==register,"unexpected dispose call");
                require(code.getTryBlocks().isEmpty(),"unexpected dispose try blocks");
                MutableMethodImplementation guarded=new MutableMethodImplementation(code);Label done=guarded.newLabelForIndex(2);
                guarded.addInstruction(1,new BuilderInstruction21t(Opcode.IF_EQZ,register,done));
                direct.add(new ImmutableMethod(m.getDefiningClass(),m.getName(),m.getParameters(),m.getReturnType(),m.getAccessFlags(),m.getAnnotations(),m.getHiddenApiRestrictions(),guarded));patched++;
            }
            pool.internClass(new ImmutableClassDef(c.getType(),c.getAccessFlags(),c.getSuperclass(),c.getInterfaces(),c.getSourceFile(),c.getAnnotations(),c.getStaticFields(),c.getInstanceFields(),direct,c.getVirtualMethods()));
        }
        require(patched==1&&text.size()==5195,"unexpected replacement/bucket scope");
        FileDataStore store=new FileDataStore(output);try{pool.writeTo(store);}finally{store.close();}
        // Preserve the original per-method outgoing register budget. dexlib2 2.5
        // can undercount invoke-custom/polymorphic; no instruction is rewritten.
        DexFile serialized=DexFileFactory.loadDexFile(output,opcodes);
        try(RandomAccessFile file=new RandomAccessFile(output,"rw")){
            for(ClassDef c:serialized.getClasses())for(Method m:c.getMethods())if(m.getImplementation()!=null){
                Integer words=outgoing.get(key(m));require(words!=null,"unexpected method");int at=codeOffset(m.getImplementation())+4;
                file.seek(at);file.write(words&255);file.write(words>>>8);methods++;
            }
        }
        byte[] bytes=Files.readAllBytes(output.toPath());byte[] digest=java.security.MessageDigest.getInstance("SHA-1").digest(Arrays.copyOfRange(bytes,32,bytes.length));System.arraycopy(digest,0,bytes,12,20);
        java.util.zip.Adler32 checksum=new java.util.zip.Adler32();checksum.update(bytes,12,bytes.length-12);ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).putInt(8,(int)checksum.getValue());Files.write(output.toPath(),bytes);
        DexFile after=DexFileFactory.loadDexFile(output,opcodes);Set<String> types=new TreeSet<String>();int unchanged=0;
        List<String> omissions=new ArrayList<String>();
        for(ClassDef c:after.getClasses()){
            types.add(c.getType());String b=text.get(c.getType());require(b!=null,"new class");
            String a=render(restoreTypedDefaults(originalClasses.get(c.getType()),c,omissions));
            if(c.getType().equals(TYPE)){
                require(withoutDispose(a).equals(withoutDispose(b)),"other Choreographer member changed");
                require(a.contains("if-eqz p0, :cond_"),"null guard missing");
                Files.write(Paths.get(args[2]+"-before.smali"),b.getBytes("UTF-8"));Files.write(Paths.get(args[2]+"-after.smali"),a.getBytes("UTF-8"));
            }else{require(a.equals(b),"untouched class changed: "+c.getType());unchanged++;}
        }
        require(types.equals(text.keySet()),"bucket membership changed");
        List<String> expected=Files.readAllLines(Paths.get(args[3]));Collections.sort(expected);Collections.sort(omissions);
        require(omissions.size()==94&&omissions.equals(expected),"typed default omissions differ from reviewed exact94 list");
        Files.write(Paths.get(args[2]+"-typed-default-omissions.tsv"),omissions);
        System.out.println("CHOREOGRAPHER_DISPOSE_OVERLAY=passed|patched_methods="+patched+"|bucket_classes="+types.size()+"|symbolically_equal_other_classes="+unchanged+"|reviewed_typed_default_omissions="+omissions.size()+"|preserved_outgoing_budgets="+methods+"|framework_D8=false|phone=false");
    }
}
