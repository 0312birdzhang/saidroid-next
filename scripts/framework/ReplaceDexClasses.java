import java.io.File;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import org.jf.dexlib2.DexFileFactory;
import org.jf.dexlib2.Opcodes;
import org.jf.dexlib2.iface.ClassDef;
import org.jf.dexlib2.iface.DexFile;
import org.jf.dexlib2.iface.Method;
import org.jf.dexlib2.iface.instruction.Instruction;
import org.jf.dexlib2.writer.pool.DexPool;
import org.jf.dexlib2.writer.io.FileDataStore;

/** Replace only named ClassDefs; keep every other original ClassDef as input.
 * DexPool widens const-string instructions and fixes code offsets when needed,
 * unlike the old dx merger which fails at the 65536 string index boundary.
 */
public final class ReplaceDexClasses {
    public static void main(String[] args) throws Exception {
        Opcodes opcodes = Opcodes.forApi(23);
        DexFile original = DexFileFactory.loadDexFile(new File(args[0]), opcodes);
        DexFile patch = DexFileFactory.loadDexFile(new File(args[1]), opcodes);
        Map<String, ClassDef> replacements = new HashMap<String, ClassDef>();
        for (ClassDef definition : patch.getClasses()) replacements.put(definition.getType(), definition);
        Set<String> allowed = new HashSet<String>();
        allowed.add("Landroid/graphics/Typeface;");
        allowed.add("Landroid/graphics/FontListParser;");
        if(args.length>3){allowed.clear();for(String type:args[3].split(","))allowed.add(type);}
        if (!allowed.equals(replacements.keySet())) throw new AssertionError("Unexpected replacement scope");
        DexPool pool = new DexPool(opcodes);
        Set<String> types = new HashSet<String>();
        int replaced = 0;
        for (ClassDef definition : original.getClasses()) {
            types.add(definition.getType());
            ClassDef replacement = replacements.get(definition.getType());
            if (replacement != null) replaced++;
            pool.internClass(replacement == null ? definition : replacement);
        }
        if (replaced != allowed.size()) throw new AssertionError("Original classes were not present");
        FileDataStore store = new FileDataStore(new File(args[2]));
        try { pool.writeTo(store); }
        finally { store.close(); }
        DexFile result = DexFileFactory.loadDexFile(new File(args[2]), opcodes);
        Set<String> written = new HashSet<String>();
        int methods = 0, instructions = 0;
        for (ClassDef definition : result.getClasses()) {
            written.add(definition.getType());
            for (Method method : definition.getMethods()) {
                methods++;
                if (method.getImplementation() == null) continue;
                for (Instruction instruction : method.getImplementation().getInstructions()) {
                    if (instruction.getCodeUnits() <= 0) throw new AssertionError("Invalid instruction");
                    instructions++;
                }
            }
        }
        if (!types.equals(written)) throw new AssertionError("Original class inventory changed");
        System.out.println("DEX_CLASS_REPLACEMENT=PASS|replaced=" + replaced + "|classes=" + types.size()
                + "|decoded_methods=" + methods + "|decoded_instructions=" + instructions);
    }
}
