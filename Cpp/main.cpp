#include <iostream>

// for the minimal example involving the creation of a USD stage in TestFunction_StageCreation
#include "pxr/usd/usd/stage.h" 

// For TestFunction_PixarTutorial_HelloWorld
#include "pxr/usd/usdGeom/xform.h" 
#include "pxr/usd/usdGeom/sphere.h"
#include "pxr/usd/sdf/path.h"

#include "Profile/Profiler.hpp"

/*!
@brief Function reproducing the first item of the Pixar USD tutorial.
@see https://openusd.org/release/tut_helloworld.html
	 https://openusd.org/release/tut_helloworld_redux.html
*/
void TestFunction_PixarTutorial_HelloWorld()
{
	PROFILE_FUNCTION_TIME(0);

	std::cout << "** TestFunction_PixarTutorial_HelloWorld **" << std::endl;

	/* Python code from the tutorial

		from pxr import Usd, UsdGeom
		stage = Usd.Stage.CreateNew('HelloWorld.usda')
		xformPrim = UsdGeom.Xform.Define(stage, '/hello')
		spherePrim = UsdGeom.Sphere.Define(stage, '/hello/world')
		stage.GetRootLayer().Save()
	*/

	//Write the C++ equivalent of the above python code
	pxr::UsdStageRefPtr stage = pxr::UsdStage::CreateNew("HelloWorld.usda");
	pxr::UsdGeomXform xformPrim = pxr::UsdGeomXform::Define(stage, pxr::SdfPath("/hello"));
	pxr::UsdGeomSphere spherePrim = pxr::UsdGeomSphere::Define(stage, pxr::SdfPath("/hello/world"));

	std::string fileResult;
	stage->GetRootLayer()->ExportToString(&fileResult);
	std::cout << "Content of file HelloWorld.usda:\n" << fileResult << std::endl;

	stage->GetRootLayer()->Save(); // Save the stage at the same location as the application.
}

int main()
{
	std::cout << "Hello, World!" << std::endl;

	Profile::Profiler* profiler = (Profile::Profiler*)calloc(1, sizeof(Profile::Profiler));
	profiler->SetProfilerName("OpenUSD-Writing-Benchmark");

	Profile::SetProfiler(profiler);
	profiler->SetTrackName(0, "Main");
	profiler->Initialize();

	TestFunction_PixarTutorial_HelloWorld();

	profiler->End();
	profiler->Report();

	free(profiler);

	return 0;
}