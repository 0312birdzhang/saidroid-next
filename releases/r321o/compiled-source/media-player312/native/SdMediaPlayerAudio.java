import android.media.AudioAttributes;
import android.media.AudioPlaybackConfiguration;
import android.media.PlayerBase;
import android.os.Process;
import java.util.ArrayList;
import java.util.LinkedHashMap;

/** App-local player lifecycle records. Host routing/volume still come from PulseAudio. */
public final class SdMediaPlayerAudio {
    private static int nextId=1;
    private static final LinkedHashMap<Integer,AudioPlaybackConfiguration> players=new LinkedHashMap<>();
    public static synchronized Object invoke(String name,Object[] args) {
        if(name.equals("trackPlayer")) {
            PlayerBase.PlayerIdCard card=(PlayerBase.PlayerIdCard)args[0];
            if(card==null)throw new IllegalArgumentException("Null player identity");
            int id=nextId++;
            AudioPlaybackConfiguration config=new AudioPlaybackConfiguration(card,id,Process.myUid(),Process.myPid());
            players.put(id,config);
            System.err.println("SDAUDIO=player_registered|id="+id+"|pid="+Process.myPid()+"|scope=application-process");
            return id;
        }
        if(name.equals("getActivePlaybackConfigurations")) {
            ArrayList<AudioPlaybackConfiguration> active=new ArrayList<>();
            for(AudioPlaybackConfiguration config:players.values())if(config.isActive())active.add(config);
            return active;
        }
        int id=(Integer)args[0];AudioPlaybackConfiguration config=players.get(id);
        if(config==null)return null; // As Android's monitor, ignore events from released IDs.
        if(name.equals("playerAttributes"))config.handleAudioAttributesEvent((AudioAttributes)args[1]);
        else if(name.equals("playerEvent")) {
            config.handleStateEvent((Integer)args[1]);
            System.err.println("SDAUDIO=player_state|id="+id+"|state="+args[1]);
        } else if(name.equals("releasePlayer")) {
            config.handleStateEvent(AudioPlaybackConfiguration.PLAYER_STATE_RELEASED);players.remove(id);
            System.err.println("SDAUDIO=player_released|id="+id+"|remaining="+players.size());
        } else throw new IllegalArgumentException("Unknown player registry method: "+name);
        return null;
    }
}
