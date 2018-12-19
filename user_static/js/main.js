function phononVisualizer(structure) {

    //visualizer
    v = new phononwebsite.VibCrystal($('#vibcrystal'));

    //dispersion
    d = new phononwebsite.PhononHighcharts($('#vibhighcharts'));

    //phonon class
    p = new phononwebsite.PhononWebpage(v,d);


    //set dom objects phononwebsite
    p.setMaterialsList( $('#mat') );
    p.setReferencesList( $('#ref') );
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
    p.getUrlVars({json: "../../user_static/data/" + structure + ".json", name: "Phonon dispersion: "+structure});

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

    // update default settings
    $('#drawcell').click();
    $('#drawvectors').click();
    $("#amplitude_range").val("0.65");
    $("#amplitude_range").change();
    $("#speed_range").val("0.6");
    $("#speed_range").change();

    // check if webgl is available
    if ( ! Detector.webgl ) {
        Detector.addGetWebGLMessage();
    }
}
