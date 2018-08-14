$( document ).ready(function() {

    //visualizer
    v = new phononwebsite.VibCrystal($('#vibcrystal'));

    //dispersion
    d = new phononwebsite.PhononHighcharts($('#vibhighcharts'));

    //phonon class
    p = new phononwebsite.PhononWebpage(v,d);


    //set dom objects phononwebsite
    p.setAtomPositions( $('#atompos') );
    p.setLattice( $('#lattice') );

    p.setRepetitionsInput( $('#nx'), $('#ny'), $('#nz') );
    p.setUpdateButton( $('#update') );
    //p.setFileInput( $('#file-input') );
    p.setExportPOSCARButton($('#poscar'));
    p.setExportXSFButton($('#xsf'));
    p.setTitle($('#name'));

    //p.updateMenu();
    //p.loadLocalJSON(phononData);
    p.getUrlVars({json: "../../user_static/js/C2.json", name:"C2"});

    //set dom objects vibcrystal
    v.setCameraDirectionButton($('#camerax'),'x');
    v.setCameraDirectionButton($('#cameray'),'y');
    v.setCameraDirectionButton($('#cameraz'),'z');

    v.setCellCheckbox($('#drawcell'));
    //v.setWebmButton($('#webmbutton'));
    //v.setGifButton($('#gifbutton'));
    v.setArrowsCheckbox($('#drawvectors'));
    v.setArrowsInput($('#vectors_amplitude_range'));
    v.setSpeedInput($('#speed_range'));
    v.setAmplitudeInput($('#amplitude_box'),$('#amplitude_range'));
    v.setPlayPause($('#playpause'));

    // check if webgl is available
    if ( ! Detector.webgl ) {
        Detector.addGetWebGLMessage();
    }
});
