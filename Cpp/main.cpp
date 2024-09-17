#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/xform.h>
#include <pxr/usd/usdGeom/xformOp.h>
#include "Profile/Profiler.hpp"

#include <iostream>
#include <filesystem>
#include <string>

pxr::GfVec3f RandomVec3(float scaleX = 1.0, float scaleY = 1.0, float scaleZ = 1.0)
{
	return pxr::GfVec3f( scaleX, scaleY, scaleZ );
}

void AddRandomPlaceReferencesInStage(pxr::UsdStageRefPtr stage, const std::string& path, const std::string& baseName, const std::string& refUSDFilePath, int refCount = 10)
{
	PROFILE_FUNCTION_TIME(0);
	for (int i = 0; i < refCount; ++i)
	{
		std::string primPath = path + "/" + baseName + "_" + std::to_string(i);
		pxr::UsdPrim refCube = stage->OverridePrim(pxr::SdfPath(primPath));
		refCube.GetReferences().AddReference(refUSDFilePath);
		pxr::UsdGeomXformable refXform(refCube);
		refXform.AddTranslateOp(pxr::UsdGeomXformOp::PrecisionFloat).Set(RandomVec3(10, 10, 10));
		refXform.AddRotateXYZOp(pxr::UsdGeomXformOp::PrecisionFloat).Set(RandomVec3(180, 180, 180));
		refXform.AddScaleOp(pxr::UsdGeomXformOp::PrecisionFloat).Set(RandomVec3(2, 2, 2));
	}
}

pxr::UsdStageRefPtr CreateNewStage(const std::string& filePath)
{
	PROFILE_FUNCTION_TIME(0);
	return pxr::UsdStage::CreateNew(filePath);
}

struct WriteUSDStage_RepetitionTest : public Profile::RepetitionTest
{
	int nbRefs = 0;
	int nbBatch = 1;
	int rep = 0;
	std::string usdExtension = "usda";

	WriteUSDStage_RepetitionTest() = default;

	inline void operator()() override
	{
		for (int fileNumber = 0; fileNumber < nbBatch; ++fileNumber)
		{
			pxr::UsdStageRefPtr stage = CreateNewStage("./Temp/Cubes_" + std::to_string(rep) + "_" + std::to_string(fileNumber) + "." + usdExtension);

			{
				PROFILE_BLOCK_TIME(Define World, 0);
				pxr::UsdGeomXform::Define(stage, pxr::SdfPath("/World"));
			}

			AddRandomPlaceReferencesInStage(stage, "/World", "Cube", "../../Assets/SimpleTransform." + usdExtension, nbRefs / nbBatch);

			{
				PROFILE_BLOCK_TIME(Save Stage, 0);
				stage->GetRootLayer()->Save();
			}
		}

		//Delete the temp folder
		std::filesystem::remove_all("./Temp");
	}

	void SetParameters(int _nbRefs, int _nbBatch, int _rep, const std::string& _usdExtension)
	{
		nbRefs = _nbRefs;
		nbBatch = _nbBatch;
		rep = _rep;
		usdExtension = _usdExtension;
	}
};

int main()
{
	Profile::Profiler* profiler = (Profile::Profiler*)calloc(1, sizeof(Profile::Profiler));
	profiler->SetProfilerName("OpenUSD-Writing-Benchmark");
	
	Profile::SetProfiler(profiler);
	profiler->SetTrackName(0, "Main");

	WriteUSDStage_RepetitionTest writeUSDStage_Rep;
	
	int nbRepeats = 10;
	std::vector<int> nbRefs = { 10 };//, 100, 1000};
	std::vector<int> nbBatch = { 1 };// , 2, 5, 10};
	std::vector<std::string> usdExtension = { "usda", "usdc" };

	Profile::RepetitionProfiler* repetitionProfiler = (Profile::RepetitionProfiler*)calloc(1, sizeof(Profile::RepetitionProfiler));
	Profile::ProfilerResults* results = (Profile::ProfilerResults*)calloc(nbRepeats, sizeof(Profile::ProfilerResults));

	repetitionProfiler->SetRepetitionResults(results);
	repetitionProfiler->PushBackRepetitionTest(&writeUSDStage_Rep);

	std::string path = "./ProfilingResults";
	std::filesystem::create_directory(path);

	for (int refs : nbRefs)
	{
		for (int batch : nbBatch)
		{
			for (const auto& ext : usdExtension)
			{
				std::cout << "refs: " << refs << ", batch: " << batch << ", ext: " << ext << std::endl;
				path = "./ProfilingResults/Refs_" + std::to_string(refs) + "_Batch_" + std::to_string(batch) + "_Ext_" + ext;
				std::filesystem::create_directories(path+"/Summary");
				std::filesystem::create_directories(path+"/Repetitions");

				writeUSDStage_Rep.SetParameters(refs, batch, nbRepeats, ext);
				repetitionProfiler->FixedCountRepetitionTesting(nbRepeats, false, true);

				repetitionProfiler->Report(nbRepeats);
				repetitionProfiler->ExportToCSV(path.c_str(), nbRepeats);
				std::cout << std::endl;
			}
		}
	}

	free(results);
	free(repetitionProfiler);
	free(profiler);

	return 0;
}
